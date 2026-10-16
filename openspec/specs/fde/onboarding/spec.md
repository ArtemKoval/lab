# fde/onboarding Specification

## Purpose

Gives the first-launch wizard that collects a working OpenRouter key and a model choice, and gives the settings panel that repeats the setup.

## Requirements

### Requirement: The wizard runs until the setup is done
When no setup-done mark exists, the app MUST show the wizard first and MUST NOT show the chat window before it ends. When a setup-done mark exists and the stored key decrypts, the app MUST go straight to the chat window.

#### Scenario: First launch shows the wizard
- **WHEN** the user starts the app and no setup-done mark exists
- **THEN** the app shows the wizard at step 1

#### Scenario: Later launch skips the wizard
- **WHEN** the user starts the app and the setup-done mark exists with a decryptable key
- **THEN** the app opens the chat window and shows no wizard

#### Scenario: Quit during step 2
- **WHEN** the user passes step 1 and quits the app before the finish action
- **THEN** the app stores nothing, and the next launch shows the wizard at step 1

### Requirement: Step 1 validates the key and holds it
Step 1 MUST show a password-style input for the OpenRouter API key. The continue action MUST validate the key with a real API call. An empty or invalid key MUST show an inline error and MUST NOT advance the wizard. A valid key MUST advance to step 2 and MUST stay in the memory of the main process until the finish action.

#### Scenario: Valid key advances
- **WHEN** the user enters a key that passes validation and continues
- **THEN** the wizard shows step 2 and holds the key in memory

#### Scenario: Invalid key blocks
- **WHEN** the user enters a key that the API rejects and continues
- **THEN** the wizard shows an inline error and stays at step 1

#### Scenario: Empty key blocks
- **WHEN** the user continues with an empty input
- **THEN** the wizard shows an inline error and stays at step 1

### Requirement: Step 2 lists the models with the default any
Step 2 MUST show the model list from the OpenRouter API, with the display name and id of each model. The default choice `any` MUST be preselected at the top. The finish action MUST store the key, the model choice, and the setup-done mark in one step, and MUST open the chat window.

#### Scenario: Default is preselected
- **WHEN** step 2 opens
- **THEN** the choice `any` is preselected at the top of the list

#### Scenario: Finish stores the setup in one step
- **WHEN** the user picks a model and finishes the wizard
- **THEN** the app stores the encrypted key, the model choice, and the setup-done mark together, and opens the chat window

### Requirement: Step 2 recovers when the model list fails
If the model list call fails, step 2 MUST show the failure reason and a retry action. The user MUST still finish with the default `any`, because the default needs no list.

#### Scenario: List failure shows a retry
- **WHEN** the model list call fails while step 2 is open
- **THEN** the wizard shows the failure reason and a retry action

#### Scenario: Finish with any while the list is down
- **WHEN** the model list failed and the user finishes with the preselected `any`
- **THEN** the wizard stores the setup and opens the chat window

### Requirement: The key is encrypted at rest
The app MUST store the key only as ciphertext from the OS keychain-backed storage in the user data folder. The app MUST NOT write the key in plain text to any file. The UI MUST show the stored key only in a masked form with the last four characters readable.

#### Scenario: File holds no plain key
- **WHEN** the app stores the key
- **THEN** no file in the user data folder contains the key as plain text

#### Scenario: Masked display
- **WHEN** the settings show the stored key
- **THEN** only the last four characters are readable

### Requirement: The app checks encryption before it stores the key
Before the first store, the app MUST ask the OS storage whether encryption is available, and MUST refuse weak storage. If encryption is not available, or the storage backend is the weak fallback, the app MUST keep the key for the current session only, MUST tell the user, and MUST store no key and no setup-done mark. The next launch MUST show the wizard at step 1.

#### Scenario: Encryption unavailable
- **WHEN** the OS reports that encrypted storage is not available and the user finishes the wizard
- **THEN** the app warns the user, keeps the key for the session, and stores no key and no setup-done mark

#### Scenario: Weak fallback backend
- **WHEN** the selected storage backend is the weak fallback and the user finishes the wizard
- **THEN** the app warns the user, keeps the key for the session, and stores no key and no setup-done mark

#### Scenario: Wizard returns after a session-only key
- **WHEN** the user ran the wizard with the key held for the session only and starts the app again
- **THEN** the app shows the wizard at step 1

### Requirement: An undecryptable key counts as absent
If the stored ciphertext fails to decrypt, the app MUST treat the key as absent, MUST delete the ciphertext, and MUST show the wizard at step 1.

#### Scenario: Ciphertext no longer decrypts
- **WHEN** the app starts and the stored ciphertext fails to decrypt
- **THEN** the app deletes the ciphertext and shows the wizard at step 1

### Requirement: The wizard can run again from settings
The settings MUST offer a repeat of the wizard. A repeat MUST show the stored key in masked form and MUST carry the stored model as the preselected choice. A cancel in the repeated wizard MUST keep the stored configuration unchanged.

#### Scenario: Repeat from settings
- **WHEN** the user starts the wizard again from the settings
- **THEN** the wizard shows the stored key masked and the stored model preselected

#### Scenario: Cancel keeps the configuration
- **WHEN** the user cancels the repeated wizard
- **THEN** the stored key and model stay unchanged

### Requirement: The settings panel shows and changes the configuration
The settings panel MUST show the masked key with its validity state. It MUST let the user change the default model from the OpenRouter model list. It MUST hold an advanced field for the API base URL override. Each change MUST persist at once.

#### Scenario: Settings show the masked key
- **WHEN** the user opens the settings panel
- **THEN** the panel shows the last four characters of the key and the validity state

#### Scenario: Default model change persists
- **WHEN** the user picks another default model in the settings panel
- **THEN** the panel stores the choice at once

#### Scenario: Base URL override persists
- **WHEN** the user enters another base URL in the advanced field
- **THEN** the panel stores the value at once, and the backend uses it from the next call
