# handover · Yxi_Entertainment

## 基础信息

- **是什么**：Yxi 分组里的第四个 agent（tmux `cc-Yxi_Entertainment`）。**没有自己的代码仓** ——
  负责 Yxi 安卓端里的**娱乐 / 运营那一块**：活动中心（签到等）、邮件（站内信）、工单、以及老板后续点名的功能。
  产出直接落在 `/root/src/workspace/Yxi/`（安卓端仓 `liang-senbei/yxi`），由 `cc-Yxi` 发版。
- **分工**（老板 2026-09-05 定；前三位见 `Yxi_pilot/handover.md`）：
  | 谁 | 管什么 |
  |---|---|
  | `cc-Yxi` | 安卓客户端主线：发版、入口、主流程、模拟器 |
  | `cc-logto_yxi` | 服务端 / 身份 / 会员：接口契约、后台、生产机 hk13。**只动 `logto_yxi/`** |
  | `cc-Yxi_pilot` | 拆出来的独立块（线路 / 装扮 / 抽奖历史）+ 三边结论汇进文档 |
  | `cc-Yxi_Entertainment`（我） | 活动中心、邮件、工单等娱乐 / 运营功能的客户端；需要接口就找 cc-logto_yxi 定形状 |
- **通讯**：`yxi-hub say <名字> "…"` / `yxi-hub all "…"` / `yxi-hub who`。⚠️ `say Yxi` 会同时匹配 `cc-Yxi` 和 `cc-logto_yxi`，**写全 `cc-Yxi`**。
- **避让**：动 `Yxi/` 里的文件先跟 cc-Yxi 说清碰哪几个；他 build 时用 `git add -A`，
  **我改了一半的文件会被他一起提交**（2026-09-05 真发生过：Badges.kt / Account.kt / SettingsScreen.kt / En.kt 被卷进 1694114）——
  改之前先说、改完立刻 build 验证、提交按路径 add。
- **组规（老板 2026-09-05，两次更新后的版本）**：
  ① 发版：全员改好了才构建、不频繁发。改完先记 `Yxi/handover.md`「待发版（攒着）」，cc-Yxi 问一圈、全员说齐了再 build + publish。
  ② **「改好了」= 过了子代理审查（Opus）+ E2E**，没过的不进清单。
  ③ 测试一律去 Mac mini（`ssh mac`），别在服务器本机起模拟器。
  ④ 各做各的任务、最后一起整理；动别人负责的文件先跟对方说。
  ⑤ **重要资料（卡密、网址 / 数据库在哪台服务器、数据库怎么连…）统一放老板 Windows（dfhzw，反向隧道 `ssh laptop` = 127.0.0.1:2222）的 `E:\资料\`**；文档里只写位置指针，真值不进 git、不贴聊天。
- **测试机改为 Mac mini（2026-09-05 起，cc-Yxi_pilot 搭的）**：`ssh mac`（反向隧道 127.0.0.1:2223）。
  安卓：`ssh mac '~/yxi-build/emu.sh start|stop|status|install <apk>|shot [名]|adb …'`，AVD「yxi」= android-34 **arm64**，
  release 正式包直接装；截图 `scp mac:yxi-build/shots/x.png .` 拉回看。iOS：Xcode 26.6 + iOS 26.5 模拟器（`xcrun simctl`）。
  详见全局 `~/.claude/CLAUDE.md` 末尾「测试机 Mac mini」。**别再在本机 Linux 起安卓模拟器**（慢、抢 CPU、qemu 会自己死 #264）。
  我这个会话 scratchpad 里的 `e2e/ui.py` / `run.sh` 是对着本机 adb 写的，下次用要把 `adb` 换成 `ssh mac '~/yxi-build/emu.sh adb …'`。
  `ssh mac` 报 refused = Mac 那头隧道断了（睡眠 / 重启），报给老板。
- **怎么跑 / 验**：`Yxi/dev/run.sh build`（只构建）· `adb install -r Yxi/android/app/build/outputs/apk/debug/app-debug.apk` ·
  `Yxi/dev/i18n-check.sh`（漏翻检查，改完文案必跑）。E2E 点按脚本在本会话 scratchpad `e2e/ui.py`（uiautomator dump → 按文字点）。
- **测试号**：`yxi-app-test@mail.yxi.keuury.com`，密码 `/root/.secrets/yxi-app-test.txt`（600）。
  发一封测试信：`ssh hk13 "cd /root/src/workplace/logto_yxi && python3 scripts/send-mail.py --to yxi-app-test@mail.yxi.keuury.com --title '…'"`
  ⚠️⚠️ 生产库已有真人（2026-09-05 起），**任何测试只打测试号，永远别用 `--all`**。

## 进度

- ✅ **老板第一个任务（2026-09-05）已随 1.1.10（versionCode 166）发版**：「我的」里邮件的**未读小红点**
  （只要点、不要数字、点进去就消）；邮件页**区分已读 / 未读 + 用户自己删信**。
  - 代码：`ui/Badges.kt`（新，红点水位）· `ui/SettingsScreen.kt`（GridEntry `badge:Int`→`dot:Boolean`；进「我的」刷一次 /api/me）·
    `ui/MailScreen.kt`（筹片 全部/未读N/已读 · 未读红点 · 读过标题压暗 · 删除 + 确认框）· `agent/Account.kt`（`deleteMail`）· `ui/En.kt`（+10 句）。
    ⚠️ 前四个被 cc-Yxi 的 1694114 一起提交了（见 TROUBLESHOOTING #1），MailScreen.kt + 一行注释由 cc-Yxi 按路径提交，随 1.1.10 上线。
  - 服务端：`POST /api/mail/<id>/delete` 由 cc-logto_yxi 当天上线（软删 `deleted_at`、未领奖励拒 409、幂等），契约 `logto_yxi/design/wallet-mail.md` 末尾。
  - **E2E（模拟器 + 真服务器 + 库里核对，截图在本会话 scratchpad `e2e/*.png`）**：
    红点有未读亮 → 进邮件页消 → 发一封新信再进「我的」重新亮 · 筹片三态正确（「已读」空态「没有已读的信」）·
    展开即标已读、红点消、标题变 Muted(60,64,67) · 带未领曦光的信只显示「先领取再删」· 普通信 / 只带码的信删除成功，
    DB `deleted_at` 已写、列表即消、未领提示 2→1 · `dev/i18n-check.sh` 一句不漏。
- ✅ **工单中心搬进会员服务 + 分类（老板 2026-09-05 拍板）**：做完、E2E 全过，**已由 cc-Yxi 提交 push（20cb938），记在 `Yxi/handover.md`「待发版（攒着）」，未发版**。
  - 老板原话：存到 hk13 可以；工单中心加分类让客户选：账号问题 / Bug 反馈 / 充值问题 / 其他问题。
  - 服务端（cc-logto_yxi 在做）：路径 **`/api/support/tickets`**（不叫 `/api/tickets`，`tickets` 在这个库里是曦光）；
    `POST` 提单 {category,text,version,device} · `GET ?limit&before` 列表（`unread` = 有没看过的官方回复，按工单 `last_read_at`）·
    `POST /<id>/read` · `POST /<id>/reply` 用户追问（replied→open）· `/api/me.unreadTickets` · 后台列表 + 回复 + 关闭。
  - 客户端：`agent/Tickets.kt` 整个重写（SSH JSONL → API；`Category` 枚举 + `parse`）· `ui/SettingsScreen.kt` 工单页重做
    （分类筹片必选 · 正文 · 隐私说明 · 我的工单列表：分类/状态/时间、未读红点、展开看回复串、追问框；工单格红点）·
    `agent/Account.kt`（`Me.unreadTickets` + `setUnreadTickets`）· `ui/Badges.kt`（水位改成按 key：MAIL / TICKETS）·
    `MainActivity.kt`（TicketsScreen 不再要 ssh）· `En.kt`（+20 句、删 3 句旧的）· `androidTest/TicketsTest.kt`（改测新解析）。
  - **隐私红线**（cc-logto_yxi 提、我照做、界面明写）：工单只带用户写的文字 + 版本号 + 机型，主机 / 密钥 / 会话内容一律不传。
  - **E2E（模拟器 + 真服务器 hk13，截图在本会话 scratchpad `e2e/2*.png`）**：提「Bug 反馈」工单 → 列表出现「Bug 反馈 · 待处理」→ 服务器 `scripts/support-reply.py reply 31 …` → 回到「我的」工单格红点亮 → 进工单列表红点 + 已回复 → 展开见「Yxi 官方」回复、返回「我的」红点消 → 追问发送 → 状态翻回待处理、服务端 support_replies 多一条 user → `close 31` → 界面「这条已关闭 —— 再补一句会重新打开」且追问框保留。`TicketsTest` 3 条在模拟器上过。
  - ⚠️ 契约与客户端的一处对齐：关闭的工单**可以追问 = 重开**（服务端语义），界面照此保留追问框、只提前说一句。
  - **Opus 审查（组规 ②）**：3 条发现全改 —— ① `Tickets.add` 改用 `Account.apiRaw`，429 `too_many_open` 单独提示「没关闭的工单太多了」，不再说成网络不通；② 标已读写回 `items[i].copy(...)` 而不是闭包里的旧 `tk`（markRead 在飞时列表可能已 reload，旧对象会盖掉新回复）；③ `items.forEach` 里加 `key(tk.id)`。编译过、i18n 归零、androidTest 编过，**三处修复已由同一审查员复核确认、无新问题**。**修复后已在 Mac mini 模拟器复验**（`ssh mac`，debug 包 rsync 过去装；工单格红点亮 → 列表红点 + 已回复 → 展开标已读、服务端 `last_read_reply_id` 推进到最新一条 → 返回红点消；截图 scratchpad `e2e/m0*.png`）。修复已由 cc-Yxi 提交（3758c42）。

- ✅ **深渊（老板 2026-09-05 拍板：星穹铁道混沌回忆的大幅简化版，周期半月）** —— PRD `design/abyss-prd.md`（v1）。**已随 1.1.13（versionCode 169）发版**（0f060aa 主体 + d6e975d 性格词/头像框）。
  - 服务端：cc-logto_yxi 在做（`/api/abyss` GET 状态 + `POST /api/abyss/floors/<n>` 结算；`abyss.json` 放赛季 / 紊流 / 弱点 / 难度 / 奖励 / 角色性格表；
    半月重置；每 3 星 `tickets_move(+2,'abyss')`，36 星限定装扮先用 tickets_5 占位）。契约路径待他给。
  - 客户端（我，已写完待编译）：`agent/Abyss.kt`（客户端 + **预估公式**：旅人 + Σ角色(基础含命座)×弱点 1.5×紊流；星数 = 上半过 1 + 下半过 1 + 两半都 ≥1.3 再 1）·
    `ui/AbyssScreen.kt`（本期卡 · 12 层列表 · 配队 Dialog：每半 0–2 位、同层不重复、另一半在用压暗 · 挑战 · 结果页借 DropStage 3 金/2 紫/1 蓝、落定帧一行字）·
    `ui/ActivityScreen.kt`（入口卡 + 新一期红点 `AbyssSeen`）· `MainActivity.kt`（Page.Abyss + 路由，cc-Yxi 放行）· `En.kt`（+31，i18n 归零）· `androidTest/AbyssTest.kt`（4 条）。
  - ⚠️ 设计决定：**服务端是唯一真相**，客户端预估只标「预计」，结果页显示服务端回的星数；两边对不上 = bug。
    角色性格表两边同一份（独舞者 / 幽火 设定里没写性格，要问老板）。
  - 契约定稿后对齐的五处：规则值全读 `rules` 块 · 性格用 `roster[].traits`（不再拿 Crowns.kt 匹配）· 半场战力 Math.round（= 契约 floor(x+0.5)）· `granted` 是「档 → 物品」· 入口红点 = 服务端 `played` 的反面（跨设备一致）。满星奖励文案从 `rules.fullReward` 读（素材没到时如实显示曦光 ×5 占位）。
  - **Opus 审查**：ship；1 should-fix（「深渊还没开」分支到不了 → 改成「取不到」）+ 3 nit（未用字段注释、刷新失败 toast）全改。
  - **E2E（Mac mini + hk13 真接口，截图 scratchpad `e2e/a*.png`）**：0 角色 → 入口卡红点 → 第 1 层只有旅人、预计 ★★ → 服务端 2 星、进度 2/36、红点消 → `test-grant.py --character yunxi --dup 3` → 第 2 层配队：云曦「命座 3 · 210 ✦」、选上半后下半锁「另一半在用」、预计 ★ 4.41×/0.77× → 服务端同样 1 星 → 累计 3 星发曦光 ×2 + 站内信「深渊 · 累计 3 星」，库里 abyss_progress / abyss_claims / tickets_ledger(reason=abyss) / mail 全对。仪器测试 AbyssTest 5 + TicketsTest 3 在 Mac 模拟器上 8/8 过。
  - ✅ 老板答复：独舞者 / 幽火 参照星穹铁道同类角色定性格词 → 我定为 **孤高 · 灵动**（花火 / 镜流）、**寂静 · 不灭**（流萤 / 黄泉），`Crowns.kt` 与服务端 abyss.json 逐字一致，4 个词进了弱点池并加了「星月紊流」「苍冥紊流」。
  - ✅ 老板答复：限定装扮做成星穹铁道「异相仲裁 · 王棋彩框头像」同款 → **头像框**装扮（新槽位 `Skins.FRAME`）。服务端 fullReward 用模板 `halo_abyss_{n}` / `深渊 · 王棋彩框 · 第 {n} 期`（每期自动换、不在祈愿池、期末停产），客户端 `ui/AvatarFrames.kt` 画：四档稀有度色顺环一圈（蓝→紫→金→红）+ 12 刻度（12 层）+ 顶上王棋（圆 + 十字），期数不同只转起始色相；`Skins.frames(ctx)` 按前缀从拥有列表里派生第 N 期的框，不用每期改客户端。顺带接上奖池里一直没渲染的「晨曦光环」（玫瑰→桃→天蓝）。`Me.kt` MeAvatar 只加 3 行（读 `Skins.frame`、光环外圈画一次，减弱动效时不转）。
  - **增量门禁**：Opus 审查 ship（正则 / 回退 / 重组 / 绘制尺寸 / 减弱动效 / i18n 全核对）；Mac E2E：装扮页「头像框」栏（不戴 使用中 · 晨曦光环 未拥有 · 王棋彩框 已拥有）→ 戴上 → 「我的」头像外圈效果（截图 `e2e/f0*.png`）→ 深渊页奖励文案「满 36 星再加 深渊 · 王棋彩框 · 第 1 期」。
    发装扮给测试号：hk13 `python3 scripts/test-grant.py yxi-app-test@mail.yxi.keuury.com --cosmetic halo_abyss_1`（cc-logto_yxi 新加的）。

- ✅ **云曦小管家（老板 2026-09-06 交办：「我的」+ 侧边栏加云曦入口，备忘录 / 提醒闹钟 / 天气等小服务，Q 版云曦像 Live2D 那样可交互；先调研）** —— 调研完成，PRD v0 `design/steward-prd.md` 等老板拍。
  - 素材：4 张 Q 版从老板 Windows（`ssh laptop`，`E:\资料\yxi_profile\小管家`）取回到 `design/steward-art/`（挥手 / 捧云 / 举杖 / 抱星睡），白底无 alpha、角色也偏白。
    洪水填充抠底失败（挖穿脸），**rembg isnet-anime 抠图成功**（venv 在本会话 scratchpad `rembg-venv/`，一张 74 秒）。
  - 三个 Opus 子代理发散（动效 / 服务 / 产品）结论收敛：动效 = 4 张整图物理 + 姿势切换、零依赖、2–3 天，最大杠杆是再要 3 张同姿势表情图（闭眼 / 笑 / 惊讶）；
    服务 v1 全纯客户端：备忘本地、`setAlarmClock` + `USE_EXACT_ALARM`、Open-Meteo 免 key + 手动选城市、签到 / 深渊 / 邮件三张状态卡；推送默认关。
  - **分工已定**（pilot 同意）：pilot 做服务层 `app/yxi/yunxi/`（Memos / Reminders / Weather，接口 `Yxi_pilot/design/yunxi-api.md`，已落地）；我做形象 + 页面 + 入口 + En。
  - **我的进展**：4 张 WebP 已进 `res/drawable-nodpi/yunxi_q_*.webp`（各 140–180 KB）；`ui/YunxiPet.kt`（整图物理 + 姿势切换 + 可选表情图 + 头像框）与 `ui/YunxiScreen.kt`（六张卡）已写完、编译过、i18n 归零（含 pilot 列的服务层文案）。
    **Opus 审查**：1 should-fix（提醒时间按手机时钟排、却按 Tz 选的时区显示 → 全部改成本机时钟 `clockStamp`）+ 1 建议（减弱动效下姿势切换与气泡改瞬切）+ 3 nit（眨眼 effect 条件内移、拖拽不再每帧起协程、200 条非 Lazy 列表接受）全改，**同一审查员复核确认，ship**。
    ✅ 入口已接（cc-Yxi a436267 之后）：MainActivity Page.Yunxi + 路由 + 两处侧栏 onYunxi + DrawerRow「云曦」+ 通知 extra `page=yunxi` 直达；SettingsScreen 五宫格第一格「云曦」；编译过、i18n 归零。✅ Mac E2E（`e2e/yunxi.sh` + 手工补：五宫格入口 → 页面 → 戳她「嗯？」→ 备忘 + 30 分钟提醒 → 城市搜索选绍兴市 → 实时天气 + 三天预报 → 签到 / 深渊 / 邮件真数据 → 侧栏入口；截图 `e2e/y0*.png`）。**已随 1.1.13（versionCode 169）发版**（df8e6ed，与 pilot 的服务层同版）。没验的：提醒到点响（pilot 的服务层负责，他的 11 条测试过）、减弱动效、深色主题。⬜ 老板四项决定（表情图 / 定位方式 / v1 六项与推送 / 入口名，入口名暂按「云曦」）。

- 🔄 **云曦 · 天气改用手机定位**（老板 2026-09-06：搜「长沙」搜到别省镇村 → 「不能用手机定位吗」）：pilot 加 `WeatherApi.locate()` / `hasLocationPermission()` + Manifest `ACCESS_COARSE_LOCATION` + 搜索补「X市」按人口排序；我在天气卡加「用当前位置」（先申请粗略定位权限 → locate → setCity → 刷新；失败按 NoLocationPermission / LocationUnavailable 写文案；标注「只用一次粗略位置，不保存」），En +6。编译过。**Mac E2E**：权限弹窗（approximate location）→ 允许 → locate() 在模拟器上回 LocationUnavailable，界面如实写「定位没拿到…手动选城市也行」（失败路径 ✓；成功路径模拟器验不了，已请 pilot 真机验并建议多 provider 回退）。**Opus 审查 ship**（无发现）；已记进 `Yxi/handover.md`「待发版（攒着）」，未提交、未发版，与 pilot 的服务层同版进。
- ✅ **云曦 · 任务看板**（老板 2026-09-06 发了 omggrow 任务看板截图：「加一个功能，像这个任务看板，提醒还有什么没做，方便随时记」）：方案 = 备忘录升级成看板，**同一份数据**。pilot 扩 Memo（Status TODO/DOING/BLOCKED/DONE · Priority HIGH/MID/LOW · dueAt · note · counts/overdue），我改界面：四栏筹片 + 数字、快速新建带优先级/截止日、卡片改状态、云曦进页说「还有 N 件没做（M 件高优先 / K 件过期）」。pilot 模型已落地（Status/Priority/dueAt/note/counts/overdue，旧 JSON 兼容）。**我的界面已写完**：`TaskBoardCard` + `TaskRow`（四栏筹片带计数 · 随手记带优先级/截止/提醒 · 卡片展开改状态/优先级/取消提醒/删除 · 过期红字）、`YunxiLines.todo()` 进页台词「还有 N 件没做（M 件高优先，K 件已过期）」/「都做完了，歇一歇」；台词停留 6→9 秒。En +22。**Opus 审查 ship**（一处 should-fix：看板的「进行中」跟工具卡片共用一句、英文成了 Running → 独立成「在做」= Doing）· 编译过 · i18n 归零 · **Mac E2E 过**（空看板 → 记一条 → 展开改状态 → 完成 → 开场白念未完成数）。**已提交 7491dce**（跟在 pilot 的数据层 5c794e3 后面），已记进 `Yxi/handover.md`「待发版（攒着）」，未发版。
    **Mac E2E 过**：记一件「高」优先截止今天 → 标题栏「还有 1 件没做」、待办 1、卡片「高」标 + 截止 09-06 → 展开切进行中 → 已完成 → 计数与筛选正确 → 再进页气泡「都做完了，歇一歇。」（截图 `e2e/b0*.png`）。⬜ Opus 审查（已交 review-yunxi）→ 记清单。

- ✅ **活动 ·「云曦节拍」音游**（老板 2026-09-06：「活动里做一个 Phigros / Orzmic 那种的，但先调研歌能不能用」）：**先答版权**（PRD `design/rhythm-prd.md` 第 1 节）：Phigros / Orzmic 的曲子是**一首一首谈的授权**（BMS 圈曲师供稿、SOUL NOTES 之类厂牌、音游联动），而且两家都自称**非商业**，曲师才肯低价甚至无偿授；我们是有会员有商城的商业 App，同样的歌是另一份合同。扒歌绝对不行（词曲著作权 + 录音制作者权两层，音游还完整播放、曲名曲师明写在选曲页）。**所以曲子自己合成**：`design/music/make_songs.py` 用 numpy 现算波形（没有采样包 / SoundFont / 第三方音频），三首（初雪 96 / 云曦 128 / 入渊 152 BPM，各 60 多秒）+ 六张谱从**同一份乐谱**导出，天生对齐；版权两层都在我们手上。**玩法**：一条固定判定线 + 四轨下落，Tap / Hold 两种音符，判定 完美(±80ms) / 不错(±160ms) / 漏了，分数=判定分+连击加成，评级 S/A/B/C。**文件**：`agent/Rhythm.kt`、`ui/RhythmScreen.kt`（新）· `assets/charts/*.json`、`res/raw/yx_*.ogg`（1.4MB）· `ui/ActivityScreen.kt` 入口卡 · `MainActivity.kt` Page.Rhythm · `ui/Glyph.kt` 音符图标 · `En.kt`（+26）。**服务端**（cc-logto_yxi 已上线，契约 `logto_yxi/design/rhythm.md`）：分数**不是客户端说了算** —— 客户端只报判定计数，服务端用同一套公式算分并发奖；校验用 **units（= notes + holds，长按两个判定）** 不是 notes。编译过 · i18n 归零 · **Mac E2E 过**（入口 → 选曲 → 一局打完 → 结算 → 上传 → 成绩回填；服务端的计数校验当场抓到我一个长按尾巴漏判的 bug，见 TROUBLESHOOTING #11）。**Opus 审查 ship**（两条必修已改：评级读 bestRating、切后台就停）· 全 S 限定气泡 `bubble_beat` 已补画法 · 已随 1.1.14 发版。
  **发版后又做了两轮（等下一版）**：`3867b67` 长按的条画到判定线为止（1.1.14 里它会拖到屏幕底下）；
  `c56ec90` **打击感**（老板第二轮要求）—— 自合成的 55ms 打击音效走 SoundPool、震动走 performHapticFeedback（完美清脆 / 不错闷 / 漏了不响不震）、
  选曲页两个开关、画面按 STYLE.md 的玻璃语言重做（轨道渐亮 · 按下余光 · 判定线三层 · 命中光环 + 上冲光柱 · 音符带高光 · 连击弹一下 · 评级浮现），
  关了系统动效则装饰全停、音符照落；顺手修掉 HUD 每帧重组。**Opus 审查 ship**（一条 should-fix 已改：两个开关用了 remember，「再来一次」会拿上一局的值 → 直接读，`73af6f0`）· 编译过 · i18n 归零 · Mac E2E 过（画面部分）。**又一轮（横版，提交 `4615014`）**：老板发了 Phigros 实机视频要求逐帧研究并改横版 —— 已落地横版 + 深色舞台 + 暖色判定线 + 冷青音符 + 分层命中爆点 + 按实测重做的打击音（22ms / 4511Hz / 6kHz 以上 30%，对齐他们的 4ms 亮击）；底栏状态栏收起；三条还原路径验过。**再一轮（提交 `85d5581`）**：判定线会动了（绕线中心转 ±2.5°、每两小节轻沉一下，缓动三次缓入缓出），关键是**音符活在线的坐标系里** —— 线动会重新指向全场音符但不改任何到达时刻，判定和服务端都不受影响（units 不变）。命中爆点按子代理逐帧实测改准（430ms、各层错峰、4 个方块边飞边变大、弧几乎不转）。整屏通铺。⚠️ **不做 Drag / Flick**：老板这轮没要求，PRD §2「只做 Tap + Hold」继续有效。**结算页也改横版了**（`24e0d08`）：横屏覆盖打谱面 + 结算，回选曲页才转回竖屏；两栏排布，计数用「大数字压小标签」；这一页同样不用主题色 getter。老板要的四块（点击动效 / 特效 / 判定线移动 / 横版美术音效）**都做完了**。⬜ **真机验手感**（音效和震动模拟器验不了：-no-audio、没马达）—— 只能老板或有真机的人听一耳朵。
- ✅ **个性化 → 装扮 → 聊天气泡**（老板 2026-09-06 发了 QQ 聊天气泡商店截图：「我的」加「个性化」，进去有装扮分类，先做聊天气泡；先设计几款，再复刻他发的两款）：`ui/Bubbles.kt`（新：`BubbleStyle` 边/尾巴/描边/玻璃/角标 + `BubbleBox` 渲染器 + `BubblePreview`，对话页与商店预览、装扮小样同一段画法）· `ui/Skins.kt`（Bubble 加 `style`，六款新气泡：心理活动框 / 云曦想想（复刻 QQ「心理活动框」「思考小睫」：白底 2dp 墨边、尾巴两个空心小圆圈，后者右下角探出 Q 版云曦头 `yunxi_q_head.webp`）/ 素描边 / 云朵 / 玻璃 / 像素）· `ui/PersonalizeScreen.kt`（新：分类页 → 气泡商店（实时预览 + 列表 + 使用）/ 其余分类走 `SkinPicker(only=)`）· `ui/SkinPicker.kt`（`only` 分栏参数、气泡小样改用真画法）· `ui/ChatScreen.kt`（UserBubble 容器换 BubbleBox，QueuedBubble 故意不换）· `MainActivity.kt`（Page.Personalize + 路由）· `ui/SettingsScreen.kt`（「我的」加「个性化」一行）· `En.kt`（+15）。编译过、i18n 归零。**Opus 审查 ship**（一处 nit：云朵边在小尺寸下一颗边泡都画不出 → 沿边均分、至少一颗，已改）。**六个 id 已由 cc-logto_yxi 进奖池**（wish.json 2026-09-06a；紫档 心理活动框 / 云曦想想 / 云朵 各 0.014，蓝档 素描边 / 玻璃 / 像素 各 0.0181；服务端名字统一带「气泡·」前缀），测试号已发前两枚。**Mac E2E：商店那条链路全过**（我的 → 个性化 → 聊天气泡 → 六款都在、未拥有标记正确 → 预览 → 使用 → 使用中 + 选中描边；截图 `scratchpad/e2e/p0*.png`），大预览里的「心理活动框」跟老板发的 QQ 那款对得上。**对话页真气泡也验通了**（用 cc-Yxi 搭的测试主机 127.0.0.1:2200 / cc-demo 会话；在此之前模拟器上主机全不可达、会话读不出来，UserBubble 根本没机会渲染）：「心理活动框」= 白底墨边 + 右下两个空心圆，「云曦想想」右下角探出 Q 版云曦。**小尺寸三处已修并复验**（探头图和尾巴圆圈按 0.55 缩 = `BubbleBox(compact)`、像素台阶再按短边收、探头款给文字多留一层右内边距 —— 原来最后一个字被小人盖住）。四个分类（气泡 / 头像框 / 终端配色 / 语包）都进得去。**已提交 d4e3abe**（按 hunk 提，没带走队友未提交的改动），已记进 `Yxi/handover.md`「待发版（攒着）」。验收四联图 `design/bubbles/聊天气泡-验收四联.png`（也送了一份到老板笔电 Downloads）。**合并后又回归冒烟过一轮**（2026-09-06 04:40，含队友全部改动的主树包）：商店六款正常；对话页真气泡这次是在 hk13 上 cc-Yxi 的**真 Claude Code 会话**里验的（多行换行、描边、探头位置都对）；任务看板四栏计数正常。

- ✅ **祈愿出货动画 +「祈愿逐项排查」·  已随 1.1.18（versionCode 174）发版；出货动画 2026-09-07 重做一遍，随 1.1.19 发**（老板 2026-09-06 发了九宫格分镜和一段自己录的视频：「这个九宫图就是展示了我希望的抽卡的全流程」「还是用视频，这样子连贯一点」「你直接完整的开做吧，中间的其他部分可以你自己画一下」）：
  - **出货流程**：抽完先出一张遮罩，**手指擦开**（12×12 格，擦到 62% 或 3.5 秒自动爆开）→ 白闪 0.18 秒 → 接一段 **0.6 秒短片**（红 / 金 / 紫 / 蓝各一段）→ 落到原来的结算卡。十连**只擦一次**，用这一批里最高的那档。⚠️ 动画纯表现层：东西在 `draw` 接口返回那一刻就已经是他的了，擦到一半退出 / 杀进程 / 断网，收藏页里都在 —— 不重发请求、不把擦完当领取条件。
  - **素材出处**（都不是扒的）：立绘是老板自己 AI 生成后发我的 `E:\资料\yxi_profile\抽卡`，rembg `isnet-anime` 抠图转 webp（`res/drawable-nodpi/yx_wish_*.webp`，各约 100KB）；四段短片是从**老板自己录的无水印版本**（`D:\录制_2026_09_06_22_54_05_711.mp4`）按 6.70 / 8.80 / 10.65 / 11.90 秒裁的（`res/raw/yx_wish_*.mp4`，四段合计 585KB）。音画对齐用互相关核过，相关系数 1.00，不用另外混音。
  - **文件**：`ui/WishReveal.kt`（新：`WipeReveal` 擦拭 + `RarityClip` 播片）· `ui/WishScreen.kt`（出货钩子 + 结算卡）· `agent/Wish.kt`（`Got.byPity`）· `ui/CardLibrary.kt`（收集计数）· `En.kt`。PRD 在 `design/gacha-prd.md`。
  - **发版前逐项排查查出的四个真 bug（老板问「十连单抽各种记数有没有 bug、抽数不够会不会提示」）**：① 曦光不够只把按钮变灰 = 静默失败 → 明说差多少、去哪儿拿；② **十连结算页不能滚** —— 立绘 + 九张小卡在 fontScale 1.5 下第 10 条在屏幕外，而且想滑一下看看会直接关窗（没有滚动的孩子吃拖动，一划变成一次点击），见 `Yxi/TROUBLESHOOTING.md` #288；③ 保底那一发看不出来（老板看到「离保底还差 3」抽完还是 3，其实中间归过零）→ cc-logto 加 `results[i].byPity`，结算页标「保底」；④ 卡牌库印「已收集 27 / 9」—— 分子是全部藏品 id 含装扮，分母只有角色数，见 #289。顺带把 `draw()` 里手抄的那份结果解析删了（新字段本来只有历史页看得见）。
  - **过关**：Opus 子代理审查两轮（第一轮 3 条：MediaPlayer 泄漏 / 死代码 / 关动画照放视频；第二轮 7 条改 6 条，第 7 条「BoxWithConstraints + heightIn 多余」也去掉并实测复验）· Mac 模拟器 E2E（单抽 / 十连 / 祈愿记录 1 条与 10 条 / 概率公示 30 档合计 100.00% / 卡牌库 9-9 / 关动画直达结果 / fontScale 1.0 与 1.5）· `dev/i18n-check.sh` 归零 · 全套 256 条发版前全绿（cc-Yxi 跑的）。
  - ⬜ **真机没看过** —— 擦拭手感和短片播放模拟器上看着对，但没在真手机上摸过。现在已上线，老板随时能试。
  - **奖池经济（cc-logto 算的，已报老板，我实测印证）**：每抽直接返还 0.934 张曦光，加上重复折算，收齐装扮的号十连净消耗约 **-2.1 张（负的，越抽越多）**。我连抽 9 次十连，余额 26 → 59。曦光不能买也不能卖，**没有收入损失**，是玩法松紧问题。三个旋钮都在服务端 `wish.json`（金档三项概率 / dupConvert 折算张数 / tenPull.base），改不用发版 —— 等老板拍手感。

- ✅ **抽卡出货重做 · 已随 1.1.19 发版**（提交 `f15ef34`，tag `v1.1.19`）：老板**连退三次**才定版，
  三次的根因写在 `design/gacha-prd.md`，一句话是 **「通用」不等于「无色」** ——
  通用的是那段**表演**（谁都要看蓄力），不是那段**颜色**。
  - **定版流程**：灰黑星星（蒙半透明的霜，看得见）→ 手指擦开 → **立刻**亮起这一抽的品质色 →
    蓄力 5.31s → 白光爆闪 → 揭晓（越稀有越长，蓝 1.09s / 红 1.96s）→ 片尾淡入结算卡底色 → 换卡。
  - **关键手法**：蓄力段用**色相旋转**染色。原片除了那团暖光都是无彩色，而色相旋转**对无彩色像素不起作用** ——
    所以只有光晕和发冠变色，背景和人物一点没动。（`colorbalance` / `colorchannelmixer` 会把整张图染色，不能用。）
  - **声音自己合成**：原片音轨是**数字静音**（实测 RMS −128dB）。`design/music/make_gacha_sfx.py`，numpy 无采样包。
  - **审查抓出七条我自己没看出来的**，三条真会炸：**收尾计时用墙钟**跟播放器无关 → 短片每次被砍掉尾巴、
    片尾淡入正好被切掉，越慢的机器越明显（`Yxi/TROUBLESHOOTING.md` #294）· **两个 Dialog 直接 if/else 换**
    中间一两帧谁都没盖住 → 录屏量到两帧 `#FCF9FC` 白闪（#295）· 霜的浓度实测对比度只有 1.55:1，星星等于看不见。
  - **验证方式换了**：不再用截图轮询（一趟三五秒、时间点全是糊的，还撞过别人的仪器测试），
    改成 **22 秒录屏逐帧量像素**（`scratchpad/e2e/pullrec.sh`）。五条全过：擦拭屏星星可见且无格纹 /
    擦完立刻是品质色 / 短片完整播到淡出 / 换卡全程无白闪且四周与画面同步 / 点一下能跳过。
  - ⬜ **声音真机没听过** —— Mac mini 的模拟器是 `-no-audio` 起的，**这台机器上永远验不了**。
    音游的打击音卡在同一条上。这两条只能老板真机听。

### 待发版改动 —— **只记在一处**：`Yxi/handover.md` 顶部「待发版（攒着）」
cc-Yxi 定的流程（2026-09-05）：修完一处不发版，自己往那节追加一行（写清是谁的）；他发版前 `yxi-hub all` 问一圈，
**全员说齐了**才 build + publish；例外只有线上崩溃 / 数据风险，破例前先报老板。这里不再另记一份清单，免得两处对不上。

### 设计决定（别改坏）
- **红点语义 = 「上次看过之后又来了新的」**，不是「还有没读完的」。水位 = 上次打开邮件页时的未读数，存本机 prefs
  `badge.mail.seen`；`unreadMail > 水位` 才亮。进邮件页、以及在页里每读掉一封都把水位抬到当前值 —— 所以「点进去就消」。
  未读数低于水位（别的设备上读掉了）要把水位压下来（`Badges.mailClamp`），否则之后新来的信会被旧水位吃掉。
- **未读和未领是两个数**（cc-logto_yxi 定的）：红点只跟未读走，未领单独一行提醒，别合并。
- **有东西没领的信不给删**（客户端不给按钮，服务端也拒 409）—— 删了就是把奖励删了。
- **删除失败不改本地列表**：没删掉就说没删掉。
- **先后顺序按 id 比，不按时间戳比**（cc-logto_yxi 提醒，这个项目已两次栽在秒精度上：`logto_yxi/TROUBLESHOOTING.md` #18、#30）。工单「未读」服务端按回复 id 判，客户端只读 `unread`，本地不做任何按时间比先后的逻辑。

## 读写信息在哪

**【只读源】** `/root/src/workspace/Yxi/`（安卓端，`handover.md` / `design/STYLE.md` 是规矩）·
`/root/src/workspace/logto_yxi/design/*.md`（接口契约：`wallet-mail.md` 站内信、`wish-checkin.md` 签到/祈愿）。
**【本项目自有可写】** 本目录只有 `handover.md` / `TROUBLESHOOTING.md`；代码全在 `Yxi/`。

## GitHub 耦合

自己没有仓。产出全部落在 `liang-senbei/yxi`（安卓端），由 cc-Yxi 提交发版。
耦合面是接口契约 `logto_yxi/design/*.md`：cc-logto_yxi 定稿，我照着实现。
