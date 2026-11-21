# ACE Music for Hermes

Install the source version of this media plugin and enable `acedatacloud-acemusic` in Hermes. Supply your own private `ACEDATACLOUD_API_KEY` from [Applications](https://platform.acedata.cloud/console/applications). Invoke `acedatacloud_acemusic_generate` with a description in `prompt`, or set `custom` with `lyric`, `style` and `title`. Each submission is paid. The same tool supports MP3 import (`upload`), a one-track `cover` and a two-track `mashup`. Pass owned track IDs for reference generation.

Use `acedatacloud_acemusic_task` to query the same task ID until terminal. The independent Git plugin is generated from this service definition. [REST contract](https://github.com/AceDataCloud/ACEMusicAPI) · [中文](zh-CN/acemusic.md)
