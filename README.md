# rotom_cam_rpc

## Discord verification bot flow
- Set environment variable `ROTOM_DISCORD_CLIENT_ID` to the client ID of the Discord application/bot that owns your Rich Presence apps. Optional: set `ROTOM_DISCORD_REQUIRED_GUILD_ID` to require users to be in your server.
- Create an allowlist file at `rpc_config/allowed_applications.json` (JSON map of application_id -> { "allowed_user_ids": ["123"] }). If the file exists, only listed application IDs/users can broadcast.
- When a user starts RPC, Rotom triggers the Discord device code flow so they approve the bot. The verified account is cached in `rpc_config/discord_auth.json` until the token expires, after which the user is prompted again.
