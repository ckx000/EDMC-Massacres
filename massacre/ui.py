import json
import l10n
import functools
import tkinter as tk
from typing import Optional
from dataclasses import dataclass

import massacre.massacre_settings
from massacre.massacre_mission_state import massacre_mission_listeners, MassacreMission
from massacre.massacre_settings import Configuration
from massacre.logger_factory import logger
from massacre.version_check import open_download_page
from theme import theme

_ = functools.partial(l10n.Translations.translate, context=__file__)

class MassacreMissionData:
    """
    Creates a "data-view" for the UI from all massacre missions. Will be used to create a table-like UI
    Done to split the calculations from the UI.
    """

    @dataclass
    class FactionState:
        
        allnum: int # 增加该派系任务数
        cmpnum: int # 增加该派系任务完成数
        killcmpcount: int # 增加该派系完成击杀数
        killcount: int
        reward: int 
        shareable_reward: int


    def __init__(self, massacre_state: dict[int, MassacreMission]):
        self.warnings: list[str] = []
        # if Log Level is set to DEBUG, this will output the current Massacre Mission State to the Log File.
        # for easy searching, you can Ctrl+F for "MASSACRE_MISSION_DATA_INPUT" and get the line below that.
        logger.debug("MassacreMissionData input below: MASSACRE_MISSION_DATA_INPUT")
        try:
            debug_message_state: dict[int, dict] = {}
            for k in massacre_state.keys():
                v = massacre_state[k]
                debug_message_state[k] = v.as_dict()
            logger.debug(json.dumps(debug_message_state))
        except Exception:
            logger.error("Failed to Log debug_message_state")
            pass
        # Faction -> <Count, Reward, ShareableReward, DistanceToMax>
        target_factions: list[str] = []
        """
        A list containing all Target Factions, as in Factions you are meant to 
        kill as part of the mission. This is used to warn the User that they
        have multiple targets and should recheck their stack.
        """
        target_types: list[str] = []
        """
        List of all target types (like Civilian, Pirates, etc). Will warn the User if they 
        have separate stacks.
        """
        target_systems: list[str] = []
        """
        List of all target systems - as in locations where the targets need to be killed.
        This will warn the player that they should recheck their stack.
        """
        self.faction_to_count_lookup: dict[str, MassacreMissionData.FactionState] = {}
        self.stack_height = 0
        """
        The highest amount of kills needed per faction in this stack.
        """
        self.before_stack_height = 0
        """
        The SECOND-highest amount of kills needed per faction in this stack.
        This is used for the delta-Column of the highest Stack to show the negative
        delta towards the second-highest stack.
        """
        #增加任务数初始化?不太确定是否需要在这里增加
        #self.allnum = 0

        self.target_sum = 0
        """
        The amount of total mission kills (not total required kills (see stack_height))
        """
        self.reward = 0
        """
        How much the player should expect in Wing- and Non-Wing Missions
        """
        self.shareable_reward = 0
        """
        How much the player should expect in Wing-Missions
        """
        self.mission_count = len(massacre_state.values())
        """
        How many (massacre) missions does the user currently have.
        """
        self.cmpmission_count = 0 # 添加已完成任务数量合计
        self.cmpreward = 0 # 添加已完成任务奖励合计
        self.cmpshareable_reward = 0 # 添加已完成任务组队奖励合计
        self.killcmpcount = 0 # 添加合计已完成击杀

        for mission in massacre_state.values():
            mission_giver = mission.source_faction
            """This is the Faction that handed out the mission"""

            if mission_giver not in self.faction_to_count_lookup.keys():
                """If no Mission from that Faction is known yet, it will first be initialized"""
                self.faction_to_count_lookup[mission_giver] = MassacreMissionData.FactionState(0, 0, 0, 0, 0, 0)

            faction_state = self.faction_to_count_lookup[mission_giver]
            """
            Get the currently summed kill count and rewards from this faction. This might contain data
            from previous Missions from that faction, or 0,0,0 if this is the first mission.
            """
            
            faction_state.allnum += 1 # 增加该派系任务数计数
            if mission.is_completed is True: # 已完成的处理
                faction_state.cmpnum += 1 # 累加已完成的任务数
                faction_state.killcmpcount += mission.count # 累加已完成的击杀数
                self.cmpreward += mission.reward # 已完成的任务奖励累加到合计
                if mission.is_wing: # 已完成的组队任务奖励累加到合计
                    self.cmpshareable_reward += mission.reward

            faction_state.killcount += mission.count
            self.target_sum += mission.count 
            faction_state.reward += mission.reward
            # Only wing missions are considered for shareable rewards
            if mission.is_wing:
                faction_state.shareable_reward += mission.reward

            ### Add Faction, Target Type and Target System to the list if they are not 
            ### yet present. This will be later used to generate a warning if more than 
            ### one of a type is present. See "Check for Warnings block below"
            if mission.target_faction not in target_factions:
                target_factions.append(mission.target_faction)

            if mission.target_type not in target_types:
                target_types.append(mission.target_type)

            if mission.target_system not in target_systems:
                target_systems.append(mission.target_system)

            if faction_state.killcount > self.stack_height:
                self.stack_height = faction_state.killcount

        # After all Missions have been handled, iterate through the faction_to_count_lookup to calculate the Total Rewards   
        for faction_state in self.faction_to_count_lookup.values():
            self.reward += faction_state.reward
            self.shareable_reward += faction_state.shareable_reward
            self.cmpmission_count += faction_state.cmpnum # 所有已完成的任务数(每个派系的)累加合计计数
            #循环找每个派系中最大的一个合计已击杀数.来作为所有任务的合计已击杀
            if faction_state.killcmpcount > self.killcmpcount:
                self.killcmpcount = faction_state.killcmpcount

        # Check for Warnings
        if len(target_factions) > 1:
            self.warnings.append(f"{_('Multiple Target Factions')}: {', '.join(target_factions)}!")
        if len(target_types) > 1:
            self.warnings.append(f"{_('Multiple Target Types')}: {', '.join(target_types)}!")
        if len(target_systems) > 1:
            self.warnings.append(f"{_('Multiple Target Systems')}: {', '.join(target_systems)}!")

        # Calculate before_stack_height
        for faction_state in self.faction_to_count_lookup.values():
            if faction_state.killcount > self.before_stack_height and faction_state.killcount != self.stack_height:
                self.before_stack_height = faction_state.killcount
        if self.before_stack_height == 0:  # No other elements. All at max value.
            self.before_stack_height = self.stack_height


class GridUiSettings:
    """
    Subset of the entire Configuration that focuses on which information is displayed
    """
    def __init__(self, config: Configuration):
        self.sum = config.display_sum_row #修复这里的错误
        self.delta = config.display_delta_column
        self.summary = config.display_ratio_and_cr_per_kill_row
        self.mission_count = config.display_mission_count


def __get_row_width(settings: GridUiSettings) -> int:
    """
    Return how many columns wide the Table is.
    This depends on if the delta-Column should be displayed
    """
    if settings.delta:
        return 5
    return 4


def _display_no_data_info(frame: tk.Frame):
    """
    Generate the warning that is displayed if the Missions-Event has yet to be received.

    Return Row-Pointer for next row
    """

    warning_label = tk.Label(frame, text=_("Missing Active Mission Data")+"\n"+_("If you are in game, go to main menu and come back"))
    warning_label.config(foreground="yellow")
    warning_label.grid(column=0, row=0)

    return 1


def __display_data_header(frame: tk.Frame, settings: GridUiSettings, row=0):
    """
    Display the Labels of the Table
    """
    for col in range(3+ int(settings.delta)):  # 根据是否包含 delta 列调整列数
        frame.grid_columnconfigure(col,weight=0)
    frame.grid_columnconfigure(0,minsize=120, weight=1) #设定首列最小可拉伸
    # todo 看看能否在此处派系后方插入一个切换按钮
    faction_label = tk.Label(frame, text=_("Faction"))
    missionnum_label = tk.Label(frame, text=_("R/T")) # 增加任务个数
    kills_label = tk.Label(frame, text=_("KRM/REQ"))
    payout_label = tk.Label(frame, text=_("Reward (Wing)"))

    ui_elements = [faction_label, missionnum_label, kills_label, payout_label]
    if settings.delta:
        # noinspection SpellCheckingInspection
        delta_label = tk.Label(frame, text=_("Δmax"))
        ui_elements.append(delta_label)

    for i, item in enumerate(ui_elements):
        item.grid(row=row, column=i, sticky=tk.W)


def __display_row(frame: tk.Frame, faction: str, data: MassacreMissionData.FactionState, max_count: int,
                  settings: GridUiSettings, row: int, second_largest_count: int):
    """
    Draw one Data-Row for the Table
    """
    reward_str = "{:.1f}".format(float(data.reward) / 1_000_000)
    shareable_reward_str = "{:.1f}".format(float(data.shareable_reward) / 1_000_000)

    faction_label = tk.Label(frame, text=faction)
    cmpnum_sum = int(data.allnum) - int(data.cmpnum)
    missionnum_label = tk.Label(frame, text=f"{cmpnum_sum}/{data.allnum}") # 增加任务个数
    killscmp_sum =int(data.killcount) - int(data.killcmpcount)
    kills_label = tk.Label(frame, text=f"{killscmp_sum}/{data.killcount}") # 修改击杀数显示
    payout_label = tk.Label(frame, text=f"{reward_str} ({shareable_reward_str})")

    ui_elements = [faction_label, missionnum_label, kills_label, payout_label]
    sticky_settings = [tk.W, tk.W, tk.W+tk.E , tk.W, tk.E] #考虑到delta多定义一个
    if settings.delta: 
        # Calculate difference
        delta = max_count - data.killcount
        text = delta if delta > 0 else second_largest_count - max_count
        delta_label = tk.Label(frame, text=str(text))
        ui_elements.append(delta_label)
        #delta_label.grid(row=row, column=4)# 列数+1 3改4

    for i, element in enumerate(ui_elements):
        element.grid(row=row, column=i, sticky=sticky_settings[i])

def __display_cmpsum(frame: tk.Frame, data: MassacreMissionData, _settings: GridUiSettings, row: int):
    """
    增加一行显示当前已完成的任务合计
    """
    label = tk.Label(frame, text=_("CompletedSum"))
    
    cmp_num = tk.Label(frame, text=data.cmpmission_count) # 已完成任务数量
    kill_sum = tk.Label(frame, text=data.killcmpcount) # 已完成任务的击杀数量
    reward_sum_normal = "{:.1f}".format(float(data.cmpreward) / 1_000_000)
    reward_sum_wing = "{:.1f}".format(float(data.cmpshareable_reward) / 1_000_000)
    reward_sum = tk.Label(frame, text=f"{reward_sum_normal} ({reward_sum_wing})")
    for i, entry in enumerate([label, cmp_num, kill_sum, reward_sum]):
        entry.config(fg="YellowGreen")
        entry.grid(row=row, column=i, sticky=tk.W)

def __display_sum(frame: tk.Frame, data: MassacreMissionData, _settings: GridUiSettings, row: int):
    """
    Display the Sum-Row containing the Reward-Sum and the amount of Kills required.
    """
    label = tk.Label(frame, text=_("AcceptedSum"))
    allmissionnum = tk.Label(frame, text=data.mission_count)
    kill_sum = tk.Label(frame, text=data.stack_height)
    reward_sum_normal = "{:.1f}".format(float(data.reward) / 1_000_000)
    reward_sum_wing = "{:.1f}".format(float(data.shareable_reward) / 1_000_000)
    reward_sum = tk.Label(frame, text=f"{reward_sum_normal} ({reward_sum_wing})")
    sticky_settings = [tk.W, tk.E, tk.E, tk.E]
    for i, entry in enumerate([label, allmissionnum, kill_sum, reward_sum]):
        entry.config(fg="green")
        entry.grid(row=row, column=i, sticky=sticky_settings[i])


def __display_summary(frame: tk.Frame, data: MassacreMissionData, settings: GridUiSettings, row: int):
    ratio_text = "{:.2f}".format(float(data.target_sum)/float(data.stack_height))
    reward_in_millions = float(data.reward) / 1_000_000
    wing_reward_in_millions = float(data.shareable_reward) / 1_000_000
    reward_text = "{:.2f}".format(reward_in_millions/data.stack_height)
    wing_reward_text = "{:.2f}".format(wing_reward_in_millions/data.stack_height)
    label_text = f"{_('Ratio')}: {ratio_text}, {_('Reward')}: {reward_text} ({wing_reward_text}) {_('M CR/Kill.')} {data.target_sum} {_('Kills')}."

    label = tk.Label(frame, text=label_text, fg="green")
    label.grid(row=row, column=0, columnspan=__get_row_width(settings), sticky=tk.W)


def __display_warning(frame: tk.Frame, warning: str, width: int, row: int):
    label = tk.Label(frame, text=warning)
    label.config(fg="yellow")
    label.grid(column=0, columnspan=width, row=row, sticky=tk.W)


def _display_data(frame: tk.Frame, data: MassacreMissionData, settings: GridUiSettings) -> int:
    __display_data_header(frame, settings)
    row_pointer = 1
    for faction in sorted(data.faction_to_count_lookup.keys()):
        __display_row(frame, faction, data.faction_to_count_lookup[faction], data.stack_height, settings, row_pointer,
                      data.before_stack_height)
        row_pointer += 1
        # todo 以后这里做按钮切换显示,显示每个派系下面各个任务信息

    if settings.sum:
        __display_cmpsum(frame, data, settings, row_pointer)
        row_pointer += 1
        __display_sum(frame, data, settings, row_pointer)
        row_pointer += 1

    if settings.summary:
        __display_summary(frame, data, settings, row_pointer)
        row_pointer += 1
    full_width = __get_row_width(settings)

    if settings.mission_count:
        __display_mission_count(frame, data, full_width, row_pointer)
        row_pointer += 1

    for warning in data.warnings:
        __display_warning(frame, warning, full_width, row_pointer)
        row_pointer += 1

    return row_pointer


def __display_mission_count(frame: tk.Frame, data: MassacreMissionData, width: int, row: int):
    label = tk.Label(frame, text=f"{_('Mission Count')}: {data.mission_count}/20")
    #label.config(fg="white")#白色在默认白色外观下看不清,换成蓝色或淡蓝或者用edmc的主题色
    label.grid(column=0, columnspan=width, row=row, sticky=tk.W)

def _display_outdated_version(frame: tk.Frame, settings: GridUiSettings, row: int) -> int:
    sub_frame = tk.Frame(frame)
    sub_frame.grid(row=row, column=0, columnspan=__get_row_width(settings))
    sub_frame.config(pady=10)
    tk.Label(sub_frame, text=_("Massacre Plugin is Outdated")).grid(row=0, column=0, columnspan=2)
    btn_github = tk.Button(sub_frame, text=_("Go to Download"), command=open_download_page)
    btn_dismiss = tk.Button(sub_frame, text=_("Dismiss"), command=ui.notify_version_outdated_dismissed)

    for i, item in enumerate([btn_github, btn_dismiss]):
        item.grid(row=1, column=i)
    theme.update(sub_frame)
    return row+1


def _display_waiting_for_missions(frame: tk.Frame):
    tk.Label(frame, text=_("Massacre Plugin is ready.")).grid()
    return 1


class UI:
    def __init__(self):
        self.__frame: Optional[tk.Frame] = None
        self.__data: Optional[MassacreMissionData] = None
        self.__settings: GridUiSettings = GridUiSettings(massacre.massacre_settings.configuration)
        massacre.massacre_settings.configuration.config_changed_listeners.append(self.rebuild_settings)
        self.__display_outdated_version = False

    def rebuild_settings(self, config: Configuration):
        self.__settings = GridUiSettings(config)
        self.update_ui()

    def set_frame(self, frame: tk.Frame):
        # New EDMC Update seems to break frame.grid_size. It returned 0 for EDMC-PVPBot (where I reused the code from here)
        # So it will probably also return 0 here. Someone on the latest version should maybe check it.
        
        # Check if it is 0 and set it to 2. Should probably look into this further at some point.
        cspan = frame.grid_size()[1]
        #logger.debug("cspan: %s",cspan)
        if cspan < 1:
            cspan = 2
        self.__frame = tk.Frame(frame)
        #self.__frame.config(bg="red")
        self.__frame.grid(column=0, columnspan=cspan, sticky=tk.W)
        self.__frame.bind("<<Refresh>>", lambda _: self.update_ui())
        self.update_ui()

    def notify_about_new_massacre_mission_state(self, data: Optional[MassacreMissionData]):
        self.__data = data
        self.update_ui()

    def notify_about_settings_changed(self):
        self.__settings: GridUiSettings = GridUiSettings(massacre.massacre_settings.configuration)
        self.update_ui()

    def adjust_column_widths(self):
        # 动态调整列宽
        for col in range(__get_row_width(self.__settings)):
            max_width = 0
            for widget in self.frame.grid_slaves(column=col):
                width = widget.winfo_reqwidth()
                max_width = max(max_width, width)
            self.frame.grid_columnconfigure(col, minsize=max_width + 0)

    def update_ui(self):
        if self.__frame is None:
            logger.warning("Frame was not yet set. UI was not updated.")
            return

        logger.info("Updating UI...")
        # Remove all the Children in the Frame for rebuild
        for child in self.__frame.winfo_children():
            child.destroy()

        row_pointer = 0
        if self.__data is None:
            row_pointer = _display_no_data_info(self.__frame)
        elif self.__data.target_sum == 0:
            row_pointer = _display_waiting_for_missions(self.__frame)
        else:
            row_pointer = _display_data(self.__frame, self.__data, self.__settings)
            #self.adjust_column_widths()

        if self.__display_outdated_version:
            row_pointer = _display_outdated_version(self.__frame, self.__settings, row_pointer)

        theme.update(self.__frame)
        logger.info("UI Update done")

    # To be called from thread
    def notify_version_outdated(self):
        self.__display_outdated_version = True
        self.__frame.event_generate("<<Refresh>>") # type: ignore

    # To be called from Button
    def notify_version_outdated_dismissed(self):
        self.__display_outdated_version = False
        self.update_ui()


ui = UI()


def handle_new_massacre_mission_state(data: dict[int, MassacreMission]):
    data_view = MassacreMissionData(data)
    ui.notify_about_new_massacre_mission_state(data_view)


massacre_mission_listeners.append(handle_new_massacre_mission_state)
