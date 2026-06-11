# Hookdeck Fan-out Architecture Configuration

This project contains the configuration for a Fan-out Architecture in Hookdeck, created for the run-id `zr-n79pg7b`.

## Configured Resources

### 1. Source
* **Name**: `fanout-source-zr-n79pg7b`
* **ID**: `src_eo37hvbxn0ckd9`
* **Type**: `WEBHOOK`
* **URL**: `https://hkdk.events/eo37hvbxn0ckd9`

### 2. Destinations
* **Destination 1 (Mock API - 10/sec)**:
  * **Name**: `mock-dest-1-zr-n79pg7b`
  * **ID**: `des_9DUMN6zxGKqY`
  * **Type**: `MOCK_API`
  * **Rate Limit**: 10 requests per `second`
* **Destination 2 (Mock API - 5/min)**:
  * **Name**: `mock-dest-2-zr-n79pg7b`
  * **ID**: `des_zaIxVeXJ4WQM`
  * **Type**: `MOCK_API`
  * **Rate Limit**: 5 requests per `minute`
* **Destination 3 (CLI)**:
  * **Name**: `cli-dest-zr-n79pg7b`
  * **ID**: `des_GjNP4E2rKUXi`
  * **Type**: `CLI`
  * **Path**: `/`

### 3. Connections
* **Connection 1**:
  * **Name**: `conn-mock-1-zr-n79pg7b`
  * **ID**: `web_pp4ZDl4m5n7T`
  * **Source**: `fanout-source-zr-n79pg7b`
  * **Destination**: `mock-dest-1-zr-n79pg7b`
* **Connection 2**:
  * **Name**: `conn-mock-2-zr-n79pg7b`
  * **ID**: `web_5TarQoe2C9Ne`
  * **Source**: `fanout-source-zr-n79pg7b`
  * **Destination**: `mock-dest-2-zr-n79pg7b`
* **Connection 3**:
  * **Name**: `conn-cli-zr-n79pg7b`
  * **ID**: `web_DT5ojEsqr7jM`
  * **Source**: `fanout-source-zr-n79pg7b`
  * **Destination**: `cli-dest-zr-n79pg7b`
