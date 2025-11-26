## Support Portal Frontend

Next.js App Router UI for the support portal experience. It talks to the
Chalice backend via `NEXT_PUBLIC_API_BASE_URL`.

### Setup

```bash
cp example.env.local .env.local   # update API base URL / user id if needed
npm install
npm run dev
```

The development server runs on [http://localhost:3000](http://localhost:3000).

### Pages

- `/` Dashboard metrics (Total/Open/Resolved)
- `/tickets` List of the current user's tickets
- `/tickets/:id` Ticket details + comment stream
- `/tickets/create` Ticket submission form with optional file upload

### Implementation highlights

- Uses `fetch` to call the Chalice API with the `X-User-Id` header so the backend
  can scope queries to the active user.
- Attachments are converted to Base64 in the browser to keep the backend
  implementation simple (Chalice receives JSON with the encoded payload).
- `date-fns` powers the lightweight formatting helpers for table rows/comments.
