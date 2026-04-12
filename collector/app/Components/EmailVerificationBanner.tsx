"use client";

import { useAuth0 } from "@auth0/auth0-react";

export function EmailVerificationBanner() {
  const { isAuthenticated, isLoading, user } = useAuth0();

  if (isLoading || !isAuthenticated || !user) {
    return null;
  }

  const verified = user.email_verified === true;
  if (verified) {
    return null;
  }

  return (
    <div className="pointer-events-auto rounded-xl border border-amber-500/35 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
      <p className="font-medium text-amber-50">Verify your email</p>
      <p className="mt-1 text-amber-100/90">
        Check your inbox for a message from Auth0 and confirm your address before issuing an API key.
      </p>
    </div>
  );
}
