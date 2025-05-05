import openai from '$lib/openai';

export async function POST({ request }) {
  const { prompt } = await request.json();

  try {
    const completion = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content:
            'You are a smart home assistant. Interpret user commands and respond with actionable instructions.'
        },
        { role: 'user', content: prompt }
      ]
    });

    const reply = completion.choices[0].message.content;

    // Here you would add logic to execute device actions based on reply
    console.log('AI Response:', reply);

    return new Response(
      JSON.stringify({ reply }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('OpenAI Error:', error);
    return new Response(
      JSON.stringify({ reply: 'Sorry, I couldn’t process that.' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}