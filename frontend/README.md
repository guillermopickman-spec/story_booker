# Story Booker Frontend

A modern Next.js frontend application for the Story Booker AI-powered storybook generator.

## Features

- 🎨 Playful, colorful UI design
- 📝 Story generation form with customizable parameters
- 📊 Real-time progress tracking
- 📄 PDF preview and download
- 🌍 Multi-language support (English, Spanish)
- 🖨️ Print-on-Demand (POD) ready option
- 📱 Responsive mobile-friendly design

## Prerequisites

- Node.js 18+ and npm
- FastAPI backend running (see main project README)

## Local Development Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)

### 4. Start Backend Server

In a separate terminal, start the FastAPI backend:

```bash
cd ..
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The backend should be running at [http://localhost:8000](http://localhost:8000)

## Testing the Complete Flow

### 1. Start Both Servers

- Frontend: `npm run dev` (in `frontend/` directory)
- Backend: `uvicorn src.main:app --reload` (in project root)

### 2. Open the Application

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

### 3. Test Story Generation

1. **Fill in the form:**
   - Enter an optional story theme (e.g., "A brave little mouse goes on an adventure")
   - Select number of pages (1-10)
   - Choose an art style (CLAYMATION, VINTAGE_SKETCH, etc.)
   - Select language(s): English and/or Spanish
   - Optionally enable POD-ready mode

2. **Click "Generate Storybook"**
   - The form will submit and show a progress tracker

3. **Monitor Progress:**
   - Watch the progress bar and current step updates
   - Progress updates automatically every 2 seconds

4. **View and Download PDF:**
   - When generation completes, the PDF preview will appear
   - Use the download button to save the PDF
   - If multiple languages were selected, switch between them using the dropdown

### 4. Test Error Handling

- Stop the backend server to test connection errors
- Try submitting with invalid data to test validation
- Check that error messages are displayed clearly

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/               # Base UI components (Shadcn/ui style)
│   ├── GenerationForm.tsx
│   ├── ProgressTracker.tsx
│   ├── PDFPreview.tsx
│   └── StatusBadge.tsx
├── lib/                   # Utilities and API client
│   ├── api.ts            # API client functions
│   ├── types.ts          # TypeScript types
│   ├── constants.ts      # Constants (art styles, languages)
│   └── utils.ts          # Utility functions
├── hooks/                 # Custom React hooks
│   └── useJobStatus.ts   # Job status polling hook
└── public/               # Static assets
```

## Build for Production

```bash
npm run build
npm start
```

## Deployment

See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) for Vercel deployment instructions.

## Technologies Used

- **Next.js 16** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **React Hook Form** - Form handling
- **Zod** - Schema validation
- **Lucide React** - Icons

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
