"use client";

import { useState } from "react";
// Import 'api' AND 'useUtils'
import { api } from "~/trpc/react";

import type { Credential, AwardHistory as IAwardHistory } from "~/trpc/shared";
import Icon from "../icon";

export const AwardHistory = ({ credential }: { credential: Credential }) => {
  const [query, setQuery] = useState<string>("");
  const { data: awards } = api.award.index.useQuery({
    credentialId: credential.docId,
    query,
  });

  // 1. Get the tRPC "utils" context.
  // This is a helper object for managing queries.
  const utils = api.useUtils();

  // 2. This hook now finds the 'delete' procedure you just built!
  const deleteMutation = api.award.delete.useMutation({
    // 3. 'onSuccess' runs AFTER your backend mutation succeeds
    onSuccess: () => {
      // 4. This is the most important part!
      // It tells tRPC to "invalidate" (mark as stale)
      // the 'award.index' query. This triggers a refetch.
      console.log("Award deleted! Refreshing list...");
      utils.award.index.invalidate({ credentialId: credential.docId });
    },
    // 5. It's always good to handle errors
    onError: (error) => {
      console.error("Failed to delete award:", error.message);
      alert("Error: Could not delete award.");
    },
  });

  // 6. This is the function we will pass to our list items
  const handleDelete = (docId: string) => {
    // Optional: Add a confirmation dialog
    if (window.confirm("Are you sure you want to delete this award?")) {
      // 7. This is what calls your backend API!
      // The object { id: awardId } MUST match your deleteAwardSchema
      deleteMutation.mutate(docId);
    }
  };

  return (
    <section className="flex flex-col gap-6">
      {/* ... (your search form is unchanged) ... */}
      <form onSubmit={(e) => e.preventDefault()}>
        <label className="sr-only" htmlFor="recipient-search">
          Search in recipients
        </label>
        <div className="relative">
          <span className="absolute left-4 top-1/2 z-10 -translate-y-1/2">
            <Icon name="magnifier" className="text-gray-5" />
          </span>
          <input
            className="block w-[27rem] rounded py-3 pl-7 pr-4 text-base text-neutral-5 outline outline-1 outline-gray-5 transition placeholder:text-gray-5 focus:outline-2 focus:outline-blue-4"
            id="recipient-search"
            type="search"
            placeholder="Search in recipients"
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </form>

      <table className="w-full table-auto border-y border-gray-2 text-gray-5">
        <thead className="font-bold">
          <tr>
            <td className="px-3 py-4">Recipient Name</td>
            <td className="px-3 py-4">Status</td>
            <td className="px-3 py-4">Awarded on</td>
            {/* 8. Add a header for the "Actions" column */}
            <td className="px-3 py-4 text-right">Actions</td>
          </tr>
        </thead>
        <tbody>
          {awards?.map((award) => (
            <AwardListItem
              // 9. You need a stable 'key'. The 'id' is perfect for this.
              key={award.docId} // *ASSUMING award.id exists!
              award={award}
              // 10. Pass the handler and mutation status to the child
              onDelete={() => handleDelete(award.docId)} // *See assumption below
              isDeleting={deleteMutation.isLoading}
            />
          ))}
        </tbody>
      </table>
    </section>
  );
};

// 11. Update the props for AwardListItem to accept the new function
const AwardListItem = ({
  award,
  onDelete,
  isDeleting,
}: {
  award: IAwardHistory[number];
  onDelete: () => void;
  isDeleting: boolean;
}) => {
  const {
    credentialSubject: { profile },
    awardedDate,
  } = award;

  const name =
    profile?.name ??
    ([profile?.givenName, profile?.familyName]
      .filter((n) => n)
      .join(" ")
      .trim() ||
      "Anonymous User");

  return (
    <tr className="border-t border-gray-2">
      {/* ... (Name, Status, Awarded on tds are unchanged) ... */}
      <td className="px-3 py-4">
        <p className="font-medium text-neutral-5">{name}</p>
        {profile?.email && <p>{profile.email}</p>}
      </td>

      <td className="px-3 py-4">
        <p
          data-status={award.claimed ? "claimed" : "pending"}
          className="font-semibold before:mr-2 before:content-['\2022'] data-[status=claimed]:text-green-5 data-[status=pending]:text-gray-4"
        >
          {award.claimed ? "Claimed" : "Awaiting Claim"}
        </p>
      </td>

      <td className="px-3 py-4">
        {awardedDate && (
          <p>
            {new Date(awardedDate).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })}
          </p>
        )}
      </td>

      {/* 12. Add the new table cell with the delete button */}
      <td className="px-3 py-4 text-right">
        <button
          onClick={onDelete}
          disabled={isDeleting} // Disable button while deleting
          className="font-medium text-red-600 hover:text-red-800 disabled:opacity-50"
        >
          {isDeleting ? "Deleting..." : "Delete"}
        </button>
      </td>
    </tr>
  );
};

export default AwardHistory;