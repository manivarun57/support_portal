"use client";

import { formatDistanceToNow } from "date-fns";
import { useState } from "react";
import { Comment } from "@/lib/types";
import { createComment } from "@/lib/api";

type Props = {
  comments: Comment[];
  ticketId: string;
  onCommentAdded?: (comment: Comment) => void;
};

export function CommentList({ comments, ticketId, onCommentAdded }: Props) {
  const [newComment, setNewComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const response = await createComment(ticketId, { comment: newComment.trim() });
      setNewComment("");
      if (onCommentAdded) {
        onCommentAdded(response.comment);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add comment");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      {/* Add Comment Form */}
      <div className="section-card comment-form">
        <h3 className="comment-form-title">Add a comment</h3>
        <form onSubmit={handleSubmit}>
          <div className="comment-input-wrapper">
            <textarea
              className="comment-textarea"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Write your comment here..."
              rows={4}
              disabled={submitting}
            />
          </div>
          <div className="comment-form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || !newComment.trim()}
            >
              {submitting ? "Adding..." : "Add Comment"}
            </button>
            {error && <span className="comment-error">{error}</span>}
          </div>
        </form>
      </div>

      {/* Comments List */}
      <div className="section-card comments-list">
        {comments.length === 0 ? (
          <p className="no-comments">No comments yet.</p>
        ) : (
          comments.map((comment) => (
            <div key={comment.id} className="comment-item">
              <p className="comment-author">{comment.user_id}</p>
              <p className="comment-text">{comment.comment}</p>
              <small className="comment-time">
                {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
              </small>
            </div>
          ))
        )}
      </div>
    </>
  );
}

