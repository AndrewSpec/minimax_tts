# MiniMax TTS for Home Assistant

Custom Text-to-Speech integration using MiniMax API (speech-02-turbo and newer models) via WebSocket for minimal latency.

I previously used ElevenLabs for many months, but they don't allow cloning of any voice (e.g., a famous person's voice), so I looked for an alternative and MiniMax Audio met my requirements. There was no Home Assistant integration, so I wrote my own.

## Supported voice models

* speech-2.8-hd
* speech-2.6-hd
* speech-2.8-turbo
* speech-2.6-turbo
* speech-02-hd
* speech-02-turbo

## Installation via HACS

1. Open HACS -> Integrations.
2. Click the menu (three dots) in the top right corner -> **Custom repositories**.
3. Paste this repository's URL.
4. Select the **Integration** category.
5. Click **Add**, then install "MiniMax TTS".
6. Restart Home Assistant.

## Configuration

Go to **Settings -> Devices and Services -> Create Integration** and search for **MiniMax TTS**.
You will need:
- **API Key**: From the MiniMax Console **https://platform.minimax.io/user-center/basic-information/interface-key -> Create new secret key**
- **Voice ID**: E.g., `male-qn-qingse`: **Three dots on the end of voice row -> Copy Voice ID**

## Support My Work

If you find this integration useful, you can support my work by buying me a coffee:

<a href="https://buycoffee.to/andrewspec" target="_blank"><img src="https://buycoffee.to/static/img/share/share-button-primary.png" style="width: 351px; height: 92px" alt="Buy me a coffee on buycoffee.to"></a>

