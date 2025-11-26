"use client";

import { formatDistanceToNow } from "date-fns";
import { Comment } from "@/lib/types";

type Props = {
  comments: Comment[];
};

export function CommentList({ comments }: Props) {
  if (comments.length === 0) {
    return (
      <div className="section-card">
        <p style={{ margin: 0 }}>No comments yet.</p>
      </div>
    );
  }

  return (
    <div className="section-card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {comments.map((comment) => (
        <div key={comment.id} style={{ borderBottom: "1px solid #e2e8f0", paddingBottom: "0.75rem" }}>
          <p style={{ margin: 0, fontWeight: 600 }}>{comment.user_id}</p>
          <p style={{ margin: "0.25rem 0", color: "#475569" }}>{comment.comment}</p>
          <small style={{ color: "#94a3b8" }}>
            {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
          </small>
        </div>
      ))}
    </div>
  );
}

