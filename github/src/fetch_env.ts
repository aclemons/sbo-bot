import * as fs from 'fs';
import { SSMClient, GetParameterCommand } from '@aws-sdk/client-ssm';

const client = new SSMClient();
const input = {
  Name: '/sbobot/github-app/env',
  WithDecryption: true,
};

const run = async () => {
  const command = new GetParameterCommand(input);
  const response = await client.send(command);

  if (response.Parameter && response.Parameter.Value) {
    fs.writeFileSync('/tmp/.env', response.Parameter.Value, { encoding: 'utf8' });
  } else {
    process.exit(1);
  }
};
run();
