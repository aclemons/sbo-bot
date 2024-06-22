import * as fs from 'fs';
import { SSMClient, GetParameterCommand, GetParameterCommandOutput } from '@aws-sdk/client-ssm';

const run = async () => {
  console.log('Fetching env from ssm');

  const client = new SSMClient();
  const input = {
    Name: '/sbobot/github-app/env',
    WithDecryption: true,
  };
  const command = new GetParameterCommand(input);

  let parameter: GetParameterCommandOutput | null = null;

  await client.send(command, (error, data) => {
    if (error) {
      if (error.name === 'ParameterNotFound') {
        console.log('No env file defined in SSM');
      } else {
        console.log('Error retrieving SSM parameter', JSON.stringify(error));
        process.exit(1);
      }
    } else if (data) {
      parameter = data;
    } else {
      console.log('Error retrieving SSM parameter', JSON.stringify(error));
      process.exit(1);
    }

    if (parameter === null) {
      console.log('Writing empty .env file to /tmp');
      fs.writeFileSync('/tmp/.env', '', { encoding: 'utf8' });
    } else if (parameter?.Parameter?.Value) {
      console.log('Parameter found, writing .env file to /tmp');
      fs.writeFileSync('/tmp/.env', parameter.Parameter.Value, { encoding: 'utf8' });
    } else {
      console.log('Parameter value was empty');
      process.exit(1);
    }
  });
};
run();
