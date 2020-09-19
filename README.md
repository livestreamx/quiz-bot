Telegram Quiz-bot for on-line competitions.

# Features
* Customizable challenges for different competitions: regular (simple test quiz) or story (BDD test quiz).
* Configurable settings for whole application with Pydantic BaseSettings: through ENV or JSON-file.
* Code SOLID architecture.
* Based on SQLAlchemy with PostgreSQL.
* CLI for easy starting & usage.
* API based on Flask with index page for quiz overview.

# Usage

## Preparation

Create your VENV, activate it and execute following commands:

    docker-compose up -d db
    app db create-all
    export REMOTE_TOKEN=...
  
You will have prepared database for application execution. `REMOTE_TOKEN` param value - your Telegram BotFather API token.

## Start up

Run Quiz-bot with following command:

    app run -challenges=challenge_settings_example.json -shoutbox=shoutbox_settings_example.json
    
where `challenge_settings.json` and `shoutbox_settings.json` - special JSON files with settings (necessary format examples placed in repo with similar names).

Manually starting next challenge:

    app challenge start-next -c challenge_settings_example.json
    
Sent notification for all users, registered in Quiz-bot database:

    app challenge notification -c challenge_settings_example.json
    
Run Quiz-bot overview panel:

    app admin
    
# Contributing

Contributions are welcome.
