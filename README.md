# Crowsnest-processor-point-rotations

A crowsnest microservice that connects to MQTT broker. The main functions is to rotate points for both Radar and LIDAR sensor. The point rotation can be for example be to stabilizing the view North-up or horizontally.


## How it works

For now, this microservice just does the basics.

- Connects to MQTT
- Transform head-up matrix to north-up
- Wraps into a brefv message 
- Sending message to MQTT broker

### Typical setup: docker-compose.nmea-anavs.yml

```yaml
version: "3"
services:
  multicast-nmea:
    image: ghcr.io/mo-rise/crowsnest-connector-udp-nmea:latest
    restart: unless-stopped
    network_mode: "host"
    environment:
      - MCAST_GRP=239.192.0.3
      - MCAST_PORT=60003
      - MQTT_TOPIC_RAW=CROWSNEST/SEAHORSE/GNSS/0/RAW
      - MQTT_TOPIC_JSON=CROWSNEST/SEAHORSE/GNSS/0/JSON
```

## Development setup

To setup the development environment:

```bash
    python3 -m venv venv
    source ven/bin/activate
```

Install everything thats needed for development:

```bash
    pip install -r requirements_dev.txt
```

To run the linters:

```bash
    black main.py tests
    pylint main.py
```

To run the tests:

```bash
    no automatic tests yet...
```

Add brefv as submodule:

```bash
git submodule add <url>

# Once the project is added to your repo, you have to init and update it.
git init
git submodule add git@github.com:MO-RISE/brefv.git
git submodule update

mkdir brefv-spec
datamodel-codegen --input brefv/envelope.json --input-file-type jsonschema --output brefv-spec/envelope.py
datamodel-codegen --input brefv/messages --input-file-type jsonschema  --reuse-model --output brefv-spec/messages

```

# Program 

Function based on Open3D





## License

Apache 2.0, see [LICENSE](./LICENSE)



