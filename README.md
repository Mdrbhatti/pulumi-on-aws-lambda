# pulumi-on-aws-lambda

## Deploy

```bash
pulumi stack init
pulumi config set aws:region eu-central-1

# Deploy pulumi stack
pulumi up --diff

# Once deployment is complete, lambda function URL can be accessed like this
pulumi stack output url
```

To verify if lambda was correctly deployed, try accessing the lambda via it's function url.

```bash
$ curl $(pulumi stack output url)
{"message": "not yet implemented"}%                                                                                             
```
