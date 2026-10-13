#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
FILE_PATH="$SCRIPT_DIR/test_artifacts/test_pyramid.txt"
MIME_TYPE="text/plain"
APP_NAME="podcast_transcript_agent"
TEXT="Generate podcast from this document"
USER_ID="test_user"
SESSION_ID="session_$(date +%s)_$"

# Create a new session
echo "Creating session: $SESSION_ID"
curl -X POST -H "Content-Type: application/json" -d '{}' "http://localhost:8000/apps/$APP_NAME/users/$USER_ID/sessions/$SESSION_ID"

echo -e "\n\n" # Add some space for readability

# Base64 encode the file
BASE64_CONTENT=$(base64 -w 0 "$FILE_PATH")

# Create the JSON payload
JSON_PAYLOAD=$(cat <<EOF
{
  "app_name": "$APP_NAME",
  "user_id": "$USER_ID",
  "session_id": "$SESSION_ID",
  "new_message": {
    "role": "user",
    "parts": [
      {
        "text": "$TEXT"
      },
      {
        "text": "Podcast host name is Charlotte, expert's name is Dr Joe Sponge"
      },
      {
        "inlineData": {
          "displayName": "$(basename "$FILE_PATH")",
          "data": "$BASE64_CONTENT",
          "mimeType": "$MIME_TYPE"
        }
      }
    ]
  }
}
EOF
)

# Send the request to the agent
echo "Sending payload to session: $SESSION_ID"
echo "$JSON_PAYLOAD" | curl -X POST -H "Content-Type: application/json" -d @- http://localhost:8000/run > test_response.json
