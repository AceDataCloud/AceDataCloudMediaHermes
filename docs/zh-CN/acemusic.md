# Hermes 的 ACE Music 工具

安装媒体插件源码，使用 `hermes tools enable acedatacloud-acemusic` 启用。

登录[应用列表](https://platform.acedata.cloud/console/applications)，打开**通用应用**。首次使用时先点击**初始化通用应用**，再点击 **API KEY** 旁的复制按钮。

![获取 Ace Data Cloud API Key](https://cdn.acedata.cloud/dvc3cg.jpg)

将原始 Key 保存在当前 Hermes 配置的 `ACEDATACLOUD_API_KEY` 中。

生成工具支持提示词创作、自定义歌词、MP3 导入、单曲翻唱和双曲融合。每次提交按对应操作计费。参考创作使用自己已有的音轨 ID，查询进度使用原任务 ID。[API 文档](https://github.com/AceDataCloud/ACEMusicAPI)
