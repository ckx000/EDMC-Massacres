import os
import tkinter
import datetime as dt
from typing import Any, Optional
from os.path import basename, dirname

from massacre.mission_aggregation_helper import get_missions_for_all_cmdrs

from massacre.ui import ui
from massacre.logger_factory import logger
from massacre.massacre_settings import configuration, build_settings_ui, push_new_changes
from massacre.version_check import build_worker

import massacre.integrations.main as integrations

plugin_name = os.path.basename(os.path.dirname(__file__))
selected_cmdr: Optional[str] = None


def plugin_app(parent: tkinter.Frame) -> tkinter.Frame:
    ui.set_frame(parent)
    # Init Any Integration here
    integrations.get_all_active()

    return parent

# 在 load.py 中显式初始化一下这两个属性，防止主线程起跑太快报错
if hasattr(ui, 'version_check_done') is False:
    ui.version_check_done = False
    ui.is_version_outdated = False


#主线程安全的版本状态检测循环（使用唯一的 ui 属性，且使用已确保存在的 root_frame 挂载）
def check_version_status_loop(root_frame: tkinter.Frame, elapsed_seconds: int = 0) -> None:
    # 1. 成功检测到 ui 实例中的状态变更
    if getattr(ui, 'version_check_done', False):
        if getattr(ui, 'is_version_outdated', False):
            logger.info("Main thread detected plugin is outdated. Notifying UI...")
            try:
                ui.notify_version_outdated()
            except Exception as e:
                logger.error(f"Failed to show version notification: {str(e)}")
        else:
            logger.info("Main thread detected plugin is up to date.")
        return  # 完美收工

    # 2. 超时保护
    if elapsed_seconds >= 60:
        logger.warning("Version check timed out after 60 seconds. Stopping polling loop.")
        return

    # 3. 继续安全轮询。只要 root_frame 没销毁，就继续下个 1 秒
    try:
        if root_frame and root_frame.winfo_exists():
            root_frame.after(1000, lambda: check_version_status_loop(root_frame, elapsed_seconds + 1))
    except Exception as e:
        logger.error(f"Error in scheduling next loop: {str(e)}")


def plugin_start3(_: str) -> str:
    logger.info("Stating Massacre Plugin")
    # 根据设定决定是否在启动时检查更新
    if configuration.check_updates:
        logger.info("Starting Update Check in new Thread...")

        # 确保重置状态
        ui.version_check_done = False
        ui.is_version_outdated = False
        #def notify_ui_on_outdated(is_outdated: bool):
        def dummy_cb(is_outdated: bool):
            pass
            #if is_outdated:
            #    ui.notify_version_outdated()

        #thread = build_worker(notify_ui_on_outdated)
        thread = build_worker(dummy_cb)
        thread.start()

        # plugin_start3 执行时 EDMC 界面组件可能还没完全就绪
        # 使用 EDMC 底层的 tkinter._default_root 挂载
        try:
            import tkinter as tk
            if tk._default_root:
                tk._default_root.after(1000, lambda: check_version_status_loop(tk._default_root, 0))
        except Exception as e:
            logger.error(f"Failed to start initial loop in plugin_start3: {str(e)}")
    else:
        logger.info("Skipping Update Check. Disabled in Settings")

    # Building Mission Index
    #import datetime as dt
    mission_uuid_to_mission_lookup = get_missions_for_all_cmdrs(dt.date.today() - dt.timedelta(weeks=2))
    logger.info(f"Found Missions for {len(mission_uuid_to_mission_lookup)} CMDRs (completed, finished, failed, etc)")
    from massacre.mission_repository import set_new_repo
    set_new_repo(mission_uuid_to_mission_lookup)

    logger.info("Awaiting CMDR Name to start building Mission Index")
    return basename(dirname(__file__))


def journal_entry(cmdr: str, _is_beta: bool, _system: str,
                  _station: str, entry: dict[str, Any], _state: dict[str, Any]):
    if entry["event"] == "Missions": # 获取任务id?
        # Fetch the currently active missions and pass them to the Mission Registry
        active_mission_uuids = map(lambda x: int(x["MissionID"]), entry["Active"])
        from massacre.mission_repository import set_active_uuids
        set_active_uuids(list(active_mission_uuids), cmdr)

    elif entry["event"] == "MissionAccepted":
        # A new mission has been accepted. The Mission Repository should be notified about this
        from massacre.mission_repository import mission_repository
        if mission_repository is not None:
            mission_repository.notify_about_new_mission_accepted(entry, cmdr)

    elif entry["event"] == "MissionRedirected":
        #增加任务目标完成的处理，此处是处理“事件”
        mission_uuid = entry["MissionID"]
        from massacre.mission_repository import mission_repository
        if mission_repository is not None:
            mission_repository.notify_complete_mission_gone(mission_uuid)

    elif entry["event"] in ["MissionAbandoned", "MissionCompleted"]:
        # Mission has been completed or failed -> It is no longer active
        mission_uuid = entry["MissionID"]
        from massacre.mission_repository import mission_repository
        if mission_repository is not None:
            mission_repository.notify_about_mission_gone(mission_uuid)

    # Pass through the Event to any Integration that needs it
    for integration in integrations.get_all_active():
        try:
            integration.notify_new_event(entry)
        except Exception as e:
            logger.exception(e)


def plugin_prefs(parent: Any, _cmdr: str, _is_beta: bool):
    return build_settings_ui(parent)


def prefs_changed(_cmdr: str, _is_beta: bool):
    push_new_changes()
