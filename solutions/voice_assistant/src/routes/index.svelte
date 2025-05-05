<script>
  import { onMount } from 'svelte';
  let isListening = false;
  let transcript = '';
  let response = '';
  let recognition;

  const startListening = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Speech Recognition not supported');
      return;
    }

    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isListening = true;
      transcript = '';
      response = '';
    };

    recognition.onresult = async (event) => {
      transcript = event.results[0][0].transcript;
      isListening = false;
      await sendToAI(transcript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      isListening = false;
    };

    recognition.start();
  };

  const sendToAI = async (text) => {
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        body: JSON.stringify({ prompt: text }),
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await res.json();
      response = data.reply;
      speak(data.reply);
    } catch (err) {
      console.error(err);
      response = 'Sorry, something went wrong.';
    }
  };

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);
  };
</script>

<style>
  .btn {
    @apply px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition;
  }
</style>

<main class="p-6 max-w-xl mx-auto">
  <h1 class="text-2xl font-bold mb-4">Smart Home Assistant</h1>

  <div class="mb-4">
    <button class="btn" on:click={startListening} disabled={isListening}>
      {#if isListening}
        Listening...
      {:else}
        Start Talking
      {/if}
    </button>
  </div>

  {#if transcript}
    <div class="mb-2">
      <strong>You said:</strong> {transcript}
    </div>
  {/if}

  {#if response}
    <div>
      <strong>Assistant:</strong> {response}
    </div>
  {/if}
</main>