# ED Market Connector - Massacre Plugin/EDMC - 清缴任务插件
This is a plugin for [Elite Dangerous Market Connector](https://github.com/EDCD/EDMarketConnector).<br>
这是 [EDMC](https://github.com/EDCD/EDMarketConnector) 的一个插件

Its purpose is to help you keep track of accepted Massacre-type missions in the game "Elite Dangerous".<br>
其目的是帮助你在游戏《Elite Dangerous》中跟踪已接受的 Massacre 类型任务。

The plugin displays a table showing how many kills are required per Faction.<br>
该插件显示一个表格，展示每个派系需要多少击杀。<br>
If you are new to Massacre Stacking, you could take a look at [this article](https://sites.google.com/view/ed-pve-combat/making-money).<br>
如果您是初次接触清缴堆叠，可以阅读[这篇文章](https://tieba.baidu.com/p/9327050589).

<p align="center">
    <img src="./readme-src/example_screenshot.png" alt="An example screenshot"/>
    <br>
    Screenshot of EDMC with the Plugin running.
</p>

## Usage/用法

Simply start EDMC and the Game. If you start EDMC after the game the plugin will ask you to go
to main menu and back.<br>
只需启动 EDMC 和游戏。如果在游戏启动后才启动 EDMC，插件会要求您返回主菜单再重新进入。

From then on, start stacking missions :)<br>
For each added or abandoned / completed missions the Table will update.<br>
The status will also update each time the mission kill count is completed.<br>
从那时起，开始堆叠任务 :)<br>
每添加或放弃/完成任务时，表格都会更新。<br>
每个任务的击杀数量完成时也会更新状态

### How to read/如何查看

Below you can see the main table's explanation:<br>
下面你可以看到关于表格的解释：

<p align="center">
    <img src="./readme-src/main_table_explanations.png" alt="Main Table Explained"/>
    <br>
</p>

1. These are the mission givers<br>
    这些是任务发布者,显示为各个派系<br>
   These are the faction's mission counts,  display Missions with `Remaining with uncompleted target kills. / Total number of missions for this faction`<br>
    这些是该派系的任务数量,用于显示 `还剩几个未完成目标击杀数的 / 该派系任务总数`
2. This is distributed by the mission issuer:  `REMaining kills required / total kills REQuired for this faction's all missions`<br>
    这是由该任务发布者分发的:  `剩余需要完成击杀目标数的合计 / 所有清缴任务中击杀数的总和`<br>
    (因无法准确的统计个数,所以使用单个任务的数量来大致计算)
3. This is how much reward you will get upon completion, in Millions. The Value in brackets indicates how much of that is shareable with a wing.<br>
    这是完成后你将获得的奖励，以百万为单位。括号中的数值表示其中可分享给小队成员的金额。
4. This is the Delta-Column. It displays the difference to the highest stack. The highest stack shows the difference to the second-highest stack and can be identified by the `-`<br>
    这是 Delta 列。它显示与最高堆叠的差异。最高堆叠显示与第二高堆叠的差异，并可通过 `-` 标识。<br>
    The CompletedSum-row displays your current progress: `Number of missions with kill targets completed / Total kills achieved / Reward for completed portions`<br>
    已完成合计行显示你目前的进度:  `已完成击杀目标的任务个数`  `已完成的击杀数量`  `完成部分的奖励规模`
5. The AcceptedSum-Row shows show many Kills you need to do in total, and how big the total reward is.<br>
    已接任务合计行显示了你合计任务数量，总共需要完成的击杀次数，以及总奖励。
6. More details showing the stack ratio (see below), rewards normalized per required kill, and the sum of all Mission-Kills.<br>
    更多细节展示了堆叠效率（见下文）、每次所需击杀的奖励标准化值，以及所有任务击杀的总和。

**Stack-Ratio**: This figure tells you how effective you stack is. It is calculated as follows:<br>
`stack_ratio = all_mission_kills / required_kills`. It is a value >= 1. The higher, the better.
A Stack-ratio of 1 for example would be just taking missions from one faction. In the example above the stack ratio is `1.83 = sum([45, 54]) / max([45, 54])`.<br>
**堆叠效率**: 这个数值告诉你堆叠的效果如何。其计算方式如下：<br>
`stack_ratio = all_mission_kills / required_kills`.<br>
它是一个 >=1 的值。数值越高，效果越好。例如，堆叠效率为 1 意味着只从一个派系接取任务。<br>
在上面的例子中，堆叠效率为 `1.83 = sum([45, 54]) / max([45, 54])`.<br>
因为当你完成一个击杀目标时,不同派系的任务均会使击杀完成数+1

### Updates/更新
The plugin pings GitHub on Startup to check if a new version is available. The plugin will notify you in the UI if
a new version is available. You can turn off this behaviour in the Settings.<br>
该插件在启动时会向 GitHub 发送请求以检查是否有新版本可用。如果有新版本，插件会在 UI 中通知你。你可以在设置中关闭此行为。

The Version check is the only time the plugins does a Web-Call. And all it does is a GET to the [version file](./version).<br>
更新检查是本插件会唯一进行网络通信的部分。它所做的只是对[版本文件](./version)执行 GET 请求。

### File Access/文件访问
Because EDMC does not keep track of Missions the plugin will read through the last 2 weeks of logs on startup
and collect all Mission-Events.<br>
由于 EDMC 不会跟踪任务，插件将在启动时读取过去 2 周的日志并收集所有任务事件。

Also, when doing an Update-Check the `version`-File is read.<br>
此外，在进行更新检查时，会读取 `version` 文件

## Integrations/集成功能
This plugin features integrations. You can think of them as Plugins for this Plugin.<br>
Pull Requests are welcome for new integrations. Create an Issue if you have any questions :)<br>
此插件具有集成功能。你可以将它们视为该插件的插件。欢迎提交拉取请求以添加新的集成。如有任何问题，请创建一个Issue :)

### edmcoverlay (Linux)
This integration adds the option to send data to the Linux Implementation of edmcoverlay. When you pick up new missions you will get the current stack as an overlay.
Thank you [@pan-mroku](https://github.com/pan-mroku) for the Pull Request.<br>
此集成增加了将数据发送到 Linux 版 edmcoverlay 的选项。当你接取新任务时，当前堆栈将作为覆盖层显示。感谢 [@pan-mroku](https://github.com/pan-mroku) 的 Pull Request。


另外也支持windows版的edmcoverlay

##Acknowledgments
[AlphaConqueror](https://github.com/AlphaConqueror/EDMC-Massacres)<br>
[CMDR-WDX](https://github.com/CMDR-WDX/EDMC-Massacres)