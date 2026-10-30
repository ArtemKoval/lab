import { ShieldCheck } from "lucide-react";

// CRM's mark, name and the dashboard's tagline, as the header and the
// sign-in page show them.
export function Brand() {
  return (
    <>
      <ShieldCheck />
      CRM <span className="tagline">cases</span>
    </>
  );
}
