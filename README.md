# sbo-bot

> A GitHub App for automating SBo submissions.

## Setup

```sh
# Install dependencies
npm install

# Run the bot
npm start
```

## Docker

```sh
# 1. Build container
docker build -t sbo-bot .

# 2. Start container
docker run -e APP_ID=<app-id> -e PRIVATE_KEY=<pem-value> sbo-bot
```

## License

[MIT](LICENSE) © 2023 Andrew Clemons
