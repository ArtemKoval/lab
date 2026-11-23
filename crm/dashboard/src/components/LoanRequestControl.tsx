import { useCallback, useState } from "react";
import { api, type CaseCreateValues } from "../api";
import { REFRESH_MS, useLoad } from "../useLoad";
import type { LoanRequestWords } from "../vocabulary";

// The desk's run-time loan request: pick the member and one of their
// memberships, name the loan, and put the request in the queue. The words
// come from the pack's vocabulary, and so do the case type and the item
// category the payload carries. A server refusal surfaces in the form; a
// success closes it, and the queue's own refresh shows the request.
export function LoanRequestControl({
  words,
  onPosted,
}: {
  readonly words: LoanRequestWords;
  readonly onPosted?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [customerId, setCustomerId] = useState("");
  const [contractId, setContractId] = useState("");
  const [title, setTitle] = useState("");
  const [story, setStory] = useState("");
  const [price, setPrice] = useState("");
  const [refusal, setRefusal] = useState<string | null>(null);
  const loadCustomers = useCallback(() => api.listCustomers(), []);
  const loadContracts = useCallback(
    () => api.listCustomerContracts(customerId),
    [customerId],
  );
  const { data: customers } = useLoad(loadCustomers, REFRESH_MS);
  const { data: contracts } = useLoad(
    customerId ? loadContracts : noContracts,
    REFRESH_MS,
  );

  const ready =
    customerId !== "" &&
    contractId !== "" &&
    title.trim() !== "" &&
    story.trim() !== "" &&
    Number(price) > 0;

  async function submit(): Promise<void> {
    if (!ready) return;
    const values: CaseCreateValues = {
      customer_id: customerId,
      contract_id: contractId,
      case_type: words.case_type,
      summary: title.trim(),
      story: story.trim(),
      items: [
        {
          description: title.trim(),
          category: words.item_category,
          amount: Number(price),
        },
      ],
    };
    try {
      await api.createCase(values);
      setRefusal(null);
      setOpen(false);
      setTitle("");
      setStory("");
      setPrice("");
      setContractId("");
      onPosted?.();
    } catch (error) {
      setRefusal(error instanceof Error ? error.message : String(error));
    }
  }

  if (!open)
    return (
      <button
        type="button"
        onClick={() => {
          setOpen(true);
        }}
      >
        {words.label}
      </button>
    );

  return (
    <form
      aria-label={words.label}
      onSubmit={(event) => {
        event.preventDefault();
        submit().catch(() => undefined);
      }}
    >
      <label>
        {words.member_picker}
        <select
          value={customerId}
          onChange={(event) => {
            setCustomerId(event.target.value);
            setContractId("");
          }}
        >
          <option value="" disabled>
            —
          </option>
          {(customers ?? []).map((customer) => (
            <option key={customer.customer_id} value={customer.customer_id}>
              {customer.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        {words.membership_picker}
        <select
          value={contractId}
          onChange={(event) => {
            setContractId(event.target.value);
          }}
          disabled={customerId === ""}
        >
          <option value="" disabled>
            —
          </option>
          {(contracts ?? []).map((contract) => (
            <option key={contract.contract_id} value={contract.contract_id}>
              {contract.contract_id}
            </option>
          ))}
        </select>
      </label>
      <label>
        {words.title}
        <input
          value={title}
          onChange={(event) => {
            setTitle(event.target.value);
          }}
          required
        />
      </label>
      <label>
        {words.story}
        <textarea
          value={story}
          onChange={(event) => {
            setStory(event.target.value);
          }}
          required
        />
      </label>
      <label>
        {words.price}
        <input
          type="number"
          min="0"
          step="0.01"
          value={price}
          onChange={(event) => {
            setPrice(event.target.value);
          }}
          required
        />
      </label>
      {refusal !== null && (
        <p role="alert" className="refusal">
          {refusal}
        </p>
      )}
      <button type="submit" aria-disabled={!ready}>
        {words.submit}
      </button>
    </form>
  );
}

// No contracts before a member is picked: the load stays a settled promise
// with an empty list, so useLoad never asks the backend for a filtered
// read that has no customer yet.
function noContracts(): Promise<never[]> {
  return Promise.resolve([]);
}
