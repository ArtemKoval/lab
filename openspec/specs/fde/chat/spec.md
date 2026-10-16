# fde/chat Specification

## Purpose

Gives the chat window: a sidebar with conversations, streaming markdown replies, and a persistent local history.

## Requirements

### Requirement: The window always shows one active conversation
The sidebar MUST list all conversations with their titles and MUST mark the active one. After the wizard ends, the window MUST show one new empty conversation on the stored default model. After the user deletes the last conversation, the app MUST create and show one new empty conversation. A click on a conversation MUST make it active and show its messages.

#### Scenario: New chat appears
- **WHEN** the user clicks the new-chat action
- **THEN** a new empty conversation becomes active and appears in the sidebar

#### Scenario: Switch restores the view
- **WHEN** the user clicks another conversation in the sidebar
- **THEN** that conversation becomes active and the window shows its messages

#### Scenario: After the wizard ends
- **WHEN** the wizard stores the setup and opens the chat window
- **THEN** the window shows one new empty conversation on the stored default model

#### Scenario: Delete of the last conversation
- **WHEN** the user deletes the last conversation
- **THEN** the app creates one new empty conversation and shows it as active

### Requirement: Messages stream into the window
A sent message MUST appear as a user bubble at once. The reply MUST stream into an assistant bubble as the events arrive. When the stream ends, the full reply text MUST render as markdown. The stop action MUST end the stream, MUST keep the text received so far, and MUST save that text to the conversation file.

#### Scenario: Reply streams
- **WHEN** the user sends a message and the reply events arrive
- **THEN** the assistant bubble grows with each event until the stream ends

#### Scenario: Final markdown renders
- **WHEN** the reply holds a fenced code block and the stream ends
- **THEN** the bubble renders the block as a code element

#### Scenario: Stop keeps and saves partial text
- **WHEN** the user clicks stop during a stream
- **THEN** the stream ends, the bubble keeps the text received so far, and the conversation file holds that text

#### Scenario: Partial text survives a restart
- **WHEN** the user stops a stream and restarts the app
- **THEN** the conversation shows the partial assistant text

### Requirement: Failed sends stay visible with their error
A failed send MUST keep the user message in the window and MUST store it in the conversation file with no assistant reply. The window MUST show the user-readable message of the error kind. An `auth` error MUST show an action that runs the wizard again. When the backend error state shows, the window MUST show it as a banner and MUST refuse to send until the backend recovers.

#### Scenario: Rate limit during a send
- **WHEN** a send fails with the `rate` kind
- **THEN** the window keeps the user message and shows the rate limit message

#### Scenario: Auth error offers setup again
- **WHEN** a send fails with the `auth` kind
- **THEN** the window keeps the user message, shows the auth message, and shows an action that runs the wizard again

#### Scenario: Backend down refuses to send
- **WHEN** the backend error state shows and the user tries to send
- **THEN** the window shows the banner and sends no request

### Requirement: Each request carries the conversation history
Each send MUST include the prior messages of the active conversation in order, oldest first, together with the new message.

#### Scenario: Second turn carries the first
- **WHEN** the user sends a second message in a conversation
- **THEN** the request lists the first exchange before the second user message

### Requirement: History persists in the user data folder
The app MUST store each conversation as one JSON file in the user data folder, with the title, the model, and all messages in order. Each write MUST replace the whole file, so the file on disk always holds the full valid content. After a restart, the sidebar MUST list the conversations and each one MUST show its full history.

#### Scenario: Message survives a restart
- **WHEN** the user sends a message, quits, and starts the app again
- **THEN** the conversation holds the message and the reply

#### Scenario: One file per conversation
- **WHEN** the app stores three conversations
- **THEN** the user data folder holds one JSON file per conversation

#### Scenario: A crash mid-write leaves a valid file
- **WHEN** the app writes an update to a conversation file
- **THEN** the file on disk holds either the old content or the new content, and never a partial mix

### Requirement: Titles come from the first message and from edits
A new conversation MUST take its sidebar title from the first line of its first user message, cut to at most 40 characters. The rename action MUST let the user change the title in place, and the new title MUST persist.

#### Scenario: Auto title from a long message
- **WHEN** the first user message holds 100 characters in one line
- **THEN** the sidebar title holds the first 40 characters of that line

#### Scenario: Auto title from a multi-line message
- **WHEN** the first user message holds a line break
- **THEN** the sidebar title holds only the first line, cut to 40 characters

#### Scenario: Rename persists
- **WHEN** the user renames a conversation and restarts the app
- **THEN** the sidebar shows the new title

### Requirement: The user deletes conversations
The delete action MUST ask for confirmation. A confirmed delete MUST remove the conversation from the sidebar and its file from the user data folder. A cancelled delete MUST change nothing.

#### Scenario: Confirmed delete removes the file
- **WHEN** the user confirms the delete of a conversation
- **THEN** the sidebar drops it and the user data folder holds no file for it

#### Scenario: Cancelled delete changes nothing
- **WHEN** the user cancels the delete
- **THEN** the conversation stays in the sidebar and on disk

### Requirement: The model is per conversation with a stored default
A new conversation MUST start on the stored default model. The header MUST show the model of the active conversation. A change of the model MUST apply to the next request in that conversation and MUST persist with the conversation.

#### Scenario: Model change applies to the next request
- **WHEN** the user changes the model in the header and sends a message
- **THEN** the request carries the new model

#### Scenario: Model change persists
- **WHEN** the user changes the model and restarts the app
- **THEN** the conversation shows the new model

#### Scenario: New conversation takes the default
- **WHEN** the user creates a new conversation after changing the default model in the settings
- **THEN** the new conversation starts on the new default model

### Requirement: The window renders only sanitized markdown
The renderer MUST insert only sanitized output into the page. The sanitizer MUST remove script elements, event handler attributes, and URLs with the `javascript` scheme. The reply text is untrusted input.

#### Scenario: Script element in a reply
- **WHEN** a reply holds a script element and renders
- **THEN** the page holds no script element from the reply

#### Scenario: Inline event handler in a reply
- **WHEN** a reply holds an element with an inline event handler attribute and renders
- **THEN** the rendered element carries no event handler attribute

#### Scenario: JavaScript URL in a reply
- **WHEN** a reply holds a link with a `javascript` URL and renders
- **THEN** the rendered link does not carry that URL

### Requirement: The chat window runs sandboxed
The app MUST create the window with the sandbox on, context isolation on, and Node access in the page off. The page MUST receive a content security policy that blocks inline scripts. A popup request MUST open no window. A link with an `http` or `https` URL in a reply MUST open in the system browser, and the app window MUST NOT navigate to it.

#### Scenario: Window flags hold
- **WHEN** the app creates the chat window
- **THEN** the window uses the sandbox, context isolation, and no Node access in the page

#### Scenario: Content security policy blocks inline scripts
- **WHEN** the page loads
- **THEN** its content security policy blocks inline script execution

#### Scenario: Popup request is denied
- **WHEN** the page asks for a popup window
- **THEN** no window opens

#### Scenario: Link in a reply opens outside
- **WHEN** the user clicks an `https` link in a rendered reply
- **THEN** the system browser opens the URL and the app window stays on the chat
