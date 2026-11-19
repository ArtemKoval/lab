import { Sparkles } from "lucide-react";
import { SUGGESTED_QUESTIONS } from "../copilot";
import { useLabel } from "../vocabulary";

// What an empty conversation shows: a greeting by the worker's first name, and
// a few questions to start from, each sent with a click.
export function CopilotGreeting({
  name,
  onAsk,
  disabled,
}: Readonly<{
  name: string;
  onAsk: (question: string) => void;
  disabled: boolean;
}>) {
  const [first] = name.split(" ");
  const word = useLabel();
  const questions = SUGGESTED_QUESTIONS.map((question, index) =>
    index === SUGGESTED_QUESTIONS.length - 1
      ? word(
          "copilot.suggest.wording",
          "What does the contract wording say about baggage delays?",
        )
      : question,
  );
  return (
    <div className="greeting">
      <p className="greeting-hello">Hello, {first}.</p>
      <p className="greeting-lead">
        {word(
          "copilot.greeting.lead",
          "Ask me about the queue, a entry or the contract wording, or have me do the work. I work as you, so I can see and do what you can.",
        )}
      </p>
      <ul className="suggestions" aria-label="Questions to ask">
        {questions.map((question) => (
          <li key={question}>
            <button
              type="button"
              className="suggestion"
              disabled={disabled}
              onClick={() => {
                onAsk(question);
              }}
            >
              <Sparkles aria-hidden />
              <span>{question}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
