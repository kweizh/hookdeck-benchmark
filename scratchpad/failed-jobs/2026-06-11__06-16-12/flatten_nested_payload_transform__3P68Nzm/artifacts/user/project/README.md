# Flatten Nested Payload Transformation

This project sets up a Hookdeck connection that flattens a nested payload by extracting `id` and `email` from `data.user` and placing them at the root level as `user_id` and `user_email`, while removing the `data` object.

## Resources Created

- **Source**: `flatten-source-zr-3p68nzm` (type: WEBHOOK)
- **Destination**: `flatten-dest-zr-3p68nzm` (type: MOCK_API)
- **Connection**: `flatten-connection-zr-3p68nzm`
- **Transformation**: `flatten-transform-zr-3p68nzm`

## Transformation Logic

```javascript
return { event_type: data.event_type, user_id: data.data.user.id, user_email: data.data.user.email };
```

### Input Example
```json
{
  "event_type": "user_created",
  "data": {
    "user": {
      "id": "12345",
      "email": "user@example.com"
    }
  }
}
```

### Output Example
```json
{
  "event_type": "user_created",
  "user_id": "12345",
  "user_email": "user@example.com"
}
```

## Source Webhook URL

```
https://hkdk.events/w6bzn57p621qrj
```