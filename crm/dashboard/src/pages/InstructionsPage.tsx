import { api } from "../api";
import { Message } from "../components/Message";
import { useLoad } from "../useLoad";

export function InstructionsPage() {
  const { data, error } = useLoad(api.getInstructions);

  return (
    <>
      <h1>Agent instructions</h1>
      <p className="lead">
        What each case agent reads before it starts on a case, ending with the
        contents of the contract wording and the cases manual. The dispatcher
        that hands out the cases follows fixed rules and has no instructions.
        This page is read only.
      </p>
      <section className="panel" aria-labelledby="case-instructions-title">
        <h2 id="case-instructions-title">Working a case</h2>
        {data ? (
          <pre className="instructions">{data.case}</pre>
        ) : (
          <Message error={error} />
        )}
      </section>
    </>
  );
}
