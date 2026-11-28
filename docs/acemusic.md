# ACE Music for Hermes

Install the source version of this media plugin and enable `acedatacloud-acemusic` in Hermes.

Sign in to [Applications](https://platform.acedata.cloud/console/applications) and open **General Application**. If it is missing, select **Initialize General Application**. Click the copy button marked **1** beside **API KEY**.

![Button 1 copies the API key from General Application](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

Save the raw key in the active Hermes profile as `ACEDATACLOUD_API_KEY`.

Invoke `acedatacloud_acemusic_generate` with a description in `prompt`, or set `custom` with `lyric`, `style` and `title`. Each submission is paid. The same tool supports MP3 import (`upload`), a one-track `cover` and a two-track `mashup`. Pass owned track IDs for reference generation.

Use `acedatacloud_acemusic_task` to query the same task ID until terminal. The independent Git plugin is generated from this service definition. [REST contract](https://github.com/AceDataCloud/ACEMusicAPI) · [中文](zh-CN/acemusic.md)
