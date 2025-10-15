# Retrospective Insights - React Dashboard

Professional React TypeScript dashboard for AI-powered retrospective insights.

## 🚀 Features

- **Dashboard Overview**: Quick stats and recent reports
- **Reports Management**: List, view, and delete retrospective reports
- **Interactive Charts**: Visualize trends with Recharts
- **Hypothesis Cards**: Beautiful display of evidence-backed hypotheses
- **Experiment Tracking**: View suggested experiments with implementation steps
- **Async Task Monitoring**: Track background report generation and metrics sync
- **Responsive Design**: Works on desktop, tablet, and mobile

## 🛠️ Tech Stack

- **React 18** with TypeScript
- **Vite** - Fast build tool and dev server
- **React Router** - Client-side routing
- **Axios** - API client
- **Recharts** - Interactive charts
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icons

## 📦 Installation

```bash
npm install
```

## 🏃 Development

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

Make sure the backend API is running at `http://localhost:8000`

## 🔧 Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx          # Main dashboard
│   │   ├── ReportsPage.tsx        # Reports list
│   │   ├── ReportDetailPage.tsx   # Report details with charts
│   │   └── TasksPage.tsx          # Async task monitoring
│   ├── services/
│   │   └── api.ts                 # API client
│   ├── App.tsx                    # Main app with routing
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── public/                        # Static assets
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 🎨 Pages

### Dashboard (`/`)
- Overview statistics
- Recent reports
- Quick actions (sync metrics, generate report)

### Reports (`/reports`)
- List all reports
- Search functionality
- Delete reports

### Report Detail (`/reports/:id`)
- Full report view
- Interactive trend charts
- Hypothesis cards with evidence
- Experiment suggestions
- Facilitation guide

### Tasks (`/tasks`)
- Monitor async task execution
- Start new report generation
- Sync metrics
- Check task status

## 🔗 API Integration

The frontend integrates with the FastAPI backend:

- `GET /health` - Health check
- `POST /metrics/fetch` - Fetch metrics from external API
- `POST /reports/generate` - Generate report (sync)
- `GET /reports` - List reports
- `GET /reports/:id` - Get report details
- `DELETE /reports/:id` - Delete report
- `POST /tasks/reports/generate` - Generate report (async)
- `POST /tasks/metrics/sync` - Sync metrics (async)
- `GET /tasks/status/:taskId` - Get task status
- `DELETE /tasks/:taskId` - Cancel task

## 🎯 Key Components

### Dashboard
- Stats cards showing metrics
- Recent reports list
- Quick action buttons

### Report Detail
- Beautiful hypothesis cards with:
  - Confidence levels
  - Evidence links
  - Affected metrics
- Experiment cards with:
  - Implementation steps
  - Success metrics
  - Expected outcomes
- Interactive charts using Recharts

### Task Monitoring
- Real-time task status
- Start async operations
- Cancel pending tasks

## 🌈 Styling

Uses Tailwind CSS with custom theme:

- Primary color: Blue (`#0ea5e9`)
- Card-based layout
- Responsive grid system
- Smooth transitions and hover effects

## 📝 TypeScript Types

All API responses are fully typed in `src/services/api.ts`:

- `SprintMetrics`
- `TrendAnalysis`
- `Hypothesis`
- `ExperimentSuggestion`
- `RetrospectiveReport`
- `TaskStatus`

## 🧪 Building for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## 📄 License

MIT License

