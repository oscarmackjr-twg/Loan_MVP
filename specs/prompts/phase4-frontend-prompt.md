Task: Implement the React Frontend for the Loan Engine Application



You are extending the Loan Engine application (Phases 0-3 complete) with a fully

functional React frontend. Replace all placeholder page components with real

implementations. After this phase, users can log in, trigger pipeline runs,

browse results, view exceptions, manage files, and administer users — all through

the browser.





Context: What Already Exists (from Phases 0-3)



Backend API (fully implemented, running on port 8000)



All 26 endpoints are live and tested. The frontend must integrate with every one.



Authentication (5 endpoints)



POST /api/auth/login         → Token {access\_token, token\_type, user}

GET  /api/auth/me            → UserResponse

POST /api/auth/register      → UserResponse (admin only, 201)

PUT  /api/auth/users/{id}    → UserResponse (admin only)

GET  /api/auth/users         → List\[UserResponse] (?skip, ?limit, ?role, ?sales\_team\_id)



Pipeline \& Runs (7 endpoints)



POST /api/pipeline/run                                    → RunResponse

GET  /api/runs                                            → List\[RunResponse] (?skip, ?limit, ?status, ?run\_weekday)

GET  /api/runs/{run\_id}                                   → RunResponse

GET  /api/runs/{run\_id}/notebook-outputs                  → \[{name, path, type, size}]

GET  /api/runs/{run\_id}/notebook-outputs/{key}/download   → File download

GET  /api/runs/{run\_id}/archive                           → {input: \[...], output: \[...]}

GET  /api/runs/{run\_id}/archive/download                  → File download (?path=input/file.csv)



Data \& Reporting (5 endpoints)



GET  /api/summary/{run\_id}    → SummaryResponse

GET  /api/exceptions          → List\[ExceptionResponse] (?run\_id, ?exception\_type, ?severity, ?rejection\_criteria, ?skip, ?limit)

GET  /api/exceptions/export   → File download (?format=csv|xlsx, ?run\_id, ?exception\_type, ?severity)

GET  /api/loans               → List\[dict] (?run\_id, ?disposition, ?skip, ?limit)

GET  /api/sales-teams         → List\[{id, name}]

GET  /api/config              → {storage\_type, environment}



File Management (6 endpoints)



GET    /api/files/list                    → {path, area, count, files: \[...]} (?path, ?recursive, ?area)

POST   /api/files/upload                  → {filename, path, area, size, status} (?path, ?area)

GET    /api/files/download/{file\_path}    → File download (?area)

GET    /api/files/url/{file\_path}         → {path, area, url, expires\_in} (?area, ?expires\_in)

DELETE /api/files/{file\_path}             → {path, area, type, status} (?area)

POST   /api/files/mkdir                   → {path, area, status} (?path, ?area)



Response Schemas



typescript

// Auth

interface UserResponse {

&nbsp; id: number;

&nbsp; email: string;

&nbsp; username: string;

&nbsp; full\_name: string | null;

&nbsp; role: "admin" | "analyst" | "sales\_team";

&nbsp; sales\_team\_id: number | null;

&nbsp; is\_active: boolean;

}



interface Token {

&nbsp; access\_token: string;

&nbsp; token\_type: string;

&nbsp; user: UserResponse;

}



// Pipeline

interface RunResponse {

&nbsp; id: number;

&nbsp; run\_id: string;

&nbsp; status: "pending" | "running" | "completed" | "failed";

&nbsp; sales\_team\_id: number | null;

&nbsp; total\_loans: number;

&nbsp; total\_balance: number;

&nbsp; exceptions\_count: number;

&nbsp; run\_weekday: number | null;

&nbsp; run\_weekday\_name: string | null;

&nbsp; pdate: string | null;

&nbsp; last\_phase: string | null;

&nbsp; started\_at: string | null;

&nbsp; completed\_at: string | null;

&nbsp; created\_at: string;

}



interface SummaryResponse {

&nbsp; run\_id: string;

&nbsp; total\_loans: number;

&nbsp; total\_balance: number;

&nbsp; exceptions\_count: number;

&nbsp; eligibility\_checks: {

&nbsp;   total\_loans: number;

&nbsp;   eligible: number;

&nbsp;   rejected: number;

&nbsp;   projected: number;

&nbsp;   exceptions\_by\_type: Record<string, number>;

&nbsp;   exceptions\_by\_severity: Record<string, number>;

&nbsp; };

}



interface ExceptionResponse {

&nbsp; id: number;

&nbsp; seller\_loan\_number: string;

&nbsp; exception\_type: string;

&nbsp; exception\_category: string;

&nbsp; severity: "hard" | "soft";

&nbsp; message: string | null;

&nbsp; rejection\_criteria: string | null;

&nbsp; created\_at: string;

}



interface FileInfo {

&nbsp; name: string;

&nbsp; path: string;

&nbsp; type: "file" | "directory";

&nbsp; size: number;

&nbsp; last\_modified: string;

}



Frontend Scaffold (exists from Phase 0)





frontend/

├── package.json              # React 18, Vite, React Router, Axios

├── vite.config.js            # Proxy /api → localhost:8000

├── index.html

├── src/

│   ├── main.jsx              # Root render — KEEP, minor updates only

│   ├── App.jsx               # Router — REPLACE with full routing

│   ├── api/

│   │   └── client.js         # Axios instance — REPLACE with full implementation

│   ├── components/

│   │   └── Layout.jsx        # App shell — REPLACE with full implementation

│   ├── pages/

│   │   ├── LoginPage.jsx     # REPLACE

│   │   ├── DashboardPage.jsx # REPLACE

│   │   ├── RunDetailPage.jsx # REPLACE

│   │   ├── ExceptionsPage.jsx# REPLACE

│   │   ├── FilesPage.jsx     # REPLACE

│   │   └── UsersPage.jsx     # REPLACE

│   ├── hooks/

│   │   └── useAuth.js        # REPLACE with full implementation

│   └── context/

│       └── AuthContext.jsx    # REPLACE with full implementation

└── public/

&nbsp;   └── favicon.ico





Tech Stack \& Conventions



| Library | Version | Purpose |

|---------|---------|---------|

| React | 18.2+ | UI framework |

| React Router | v6.20+ | Client-side routing |

| Axios | 1.6+ | HTTP client |

| Vite | 5.0+ | Build tool and dev server |



Conventions

• Functional components only — no class components

• Hooks for all state management — useState, useEffect, useCallback, useMemo

• No additional UI libraries — use plain HTML elements with inline styles or CSS modules

• CSS approach: Create a single src/styles/global.css with a clean, professional design system

• Error handling: Every API call must have try/catch with user-visible error messages

• Loading states: Every data-fetching component must show loading indicators

• Responsive: Basic responsive layout (sidebar collapses on narrow screens)

• Accessibility: Semantic HTML, proper labels, keyboard navigation for forms

• No TypeScript — plain JSX with JSDoc comments for complex props

• File naming: PascalCase for components, camelCase for hooks and utilities





Files to Create or Modify



NEW FILES



| File | Purpose |

|------|---------|

| frontend/src/styles/global.css | Design system, layout, component styles |

| frontend/src/api/auth.js | Auth API functions (login, getMe, register, updateUser, listUsers) |

| frontend/src/api/runs.js | Run API functions (createRun, listRuns, getRun, getSummary) |

| frontend/src/api/exceptions.js | Exception API functions (list, export) |

| frontend/src/api/loans.js | Loan API functions (list by run) |

| frontend/src/api/files.js | File API functions (list, upload, download, delete, mkdir) |

| frontend/src/components/ProtectedRoute.jsx | Auth guard wrapper |

| frontend/src/components/StatusBadge.jsx | Run status indicator |

| frontend/src/components/Pagination.jsx | Reusable pagination controls |

| frontend/src/components/DataTable.jsx | Reusable sortable data table |

| frontend/src/components/Modal.jsx | Reusable modal dialog |

| frontend/src/components/LoadingSpinner.jsx | Loading indicator |

| frontend/src/components/ErrorMessage.jsx | Error display component |

| frontend/src/components/FileUploader.jsx | Drag-and-drop file upload |

| frontend/src/hooks/useApi.js | Generic API hook with loading/error state |

| frontend/src/hooks/usePagination.js | Pagination state management hook |

| frontend/src/utils/format.js | Number, date, currency formatting utilities |



REPLACE (full rewrite of Phase 0 stubs)



| File | Purpose |

|------|---------|

| frontend/src/App.jsx | Complete routing with auth guards |

| frontend/src/api/client.js | Axios instance with JWT interceptor and refresh |

| frontend/src/context/AuthContext.jsx | Full auth state management |

| frontend/src/hooks/useAuth.js | Auth hook with login/logout/user |

| frontend/src/components/Layout.jsx | Full app shell with navigation |

| frontend/src/pages/LoginPage.jsx | Login form with validation |

| frontend/src/pages/DashboardPage.jsx | Run list with filters |

| frontend/src/pages/RunDetailPage.jsx | Run detail with tabs |

| frontend/src/pages/ExceptionsPage.jsx | Exception browser with filters |

| frontend/src/pages/FilesPage.jsx | File manager |

| frontend/src/pages/UsersPage.jsx | User management (admin) |



KEEP (minor updates only)



| File | Changes |

|------|---------|

| frontend/src/main.jsx | Add global.css import |

| frontend/package.json | No changes needed |

| frontend/vite.config.js | No changes needed |

| frontend/index.html | No changes needed |





Directory Structure After Phase 4





frontend/src/

├── main.jsx

├── App.jsx

│

├── api/

│   ├── client.js                # Axios instance, interceptors, token management

│   ├── auth.js                  # Auth API calls

│   ├── runs.js                  # Run/pipeline API calls

│   ├── exceptions.js            # Exception API calls

│   ├── loans.js                 # Loan API calls

│   └── files.js                 # File management API calls

│

├── context/

│   └── AuthContext.jsx           # Auth provider with login/logout/user state

│

├── hooks/

│   ├── useAuth.js               # Auth context consumer hook

│   ├── useApi.js                # Generic API call hook (loading, error, data)

│   └── usePagination.js         # Pagination state hook

│

├── components/

│   ├── Layout.jsx               # App shell: sidebar, header, content area

│   ├── ProtectedRoute.jsx       # Auth guard for routes

│   ├── StatusBadge.jsx          # Colored status indicator

│   ├── Pagination.jsx           # Page controls

│   ├── DataTable.jsx            # Sortable data table

│   ├── Modal.jsx                # Dialog/modal

│   ├── LoadingSpinner.jsx       # Spinner

│   ├── ErrorMessage.jsx         # Error alert

│   └── FileUploader.jsx         # Drag-and-drop upload zone

│

├── pages/

│   ├── LoginPage.jsx            # Login form

│   ├── DashboardPage.jsx        # Pipeline runs list + create

│   ├── RunDetailPage.jsx        # Single run detail with tabs

│   ├── ExceptionsPage.jsx       # Exception browser

│   ├── FilesPage.jsx            # File manager

│   └── UsersPage.jsx            # Admin user management

│

├── styles/

│   └── global.css               # Full design system

│

└── utils/

&nbsp;   └── format.js                # Formatting utilities





Design System (frontend/src/styles/global.css)



Create a clean, professional design system with these characteristics:

• Color palette: Dark sidebar (#1a1a2e), white content area, blue primary (#4361ee),

&nbsp; green success (#06d6a0), red error (#ef476f), yellow warning (#ffd166), gray neutral (#6c757d)

• Typography: System font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif)

• Layout: Fixed sidebar (250px), scrollable content area, sticky header

• Tables: Alternating row colors, hover highlight, fixed header

• Forms: Consistent input styling, clear focus states, inline validation

• Cards: Subtle shadow, rounded corners, consistent padding

• Buttons: Primary (blue), secondary (gray), danger (red), disabled states

• Responsive: Sidebar collapses to hamburger menu below 768px

• Status colors: pending=gray, running=blue, completed=green, failed=red



Implement using CSS custom properties (variables) for the color palette.



css

:root {

&nbsp; --color-primary: #4361ee;

&nbsp; --color-primary-dark: #3651d4;

&nbsp; --color-success: #06d6a0;

&nbsp; --color-error: #ef476f;

&nbsp; --color-warning: #ffd166;

&nbsp; --color-neutral: #6c757d;

&nbsp; --color-sidebar: #1a1a2e;

&nbsp; --color-sidebar-text: #e0e0e0;

&nbsp; --color-sidebar-active: #4361ee;

&nbsp; --color-bg: #f5f6fa;

&nbsp; --color-white: #ffffff;

&nbsp; --color-text: #2d3436;

&nbsp; --color-text-light: #636e72;

&nbsp; --color-border: #dfe6e9;

&nbsp; --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

&nbsp; --font-mono: 'SF Mono', 'Fira Code', monospace;

&nbsp; --sidebar-width: 250px;

&nbsp; --header-height: 56px;

&nbsp; --radius: 8px;

&nbsp; --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

}





API Client Layer



frontend/src/api/client.js



javascript

/

• Axios instance with JWT authentication interceptor.

• Handles token storage, automatic header injection, and 401 redirect.

&nbsp;\*/

import axios from 'axios';



const client = axios.create({

&nbsp; baseURL: '/api',

&nbsp; timeout: 30000,

&nbsp; headers: { 'Content-Type': 'application/json' },

});



// Request interceptor: attach JWT token

client.interceptors.request.use((config) => {

&nbsp; const token = localStorage.getItem('access\_token');

&nbsp; if (token) {

&nbsp;   config.headers.Authorization = Bearer ${token};

&nbsp; }

&nbsp; return config;

});



// Response interceptor: handle 401 → redirect to login

client.interceptors.response.use(

&nbsp; (response) => response,

&nbsp; (error) => {

&nbsp;   if (error.response?.status === 401) {

&nbsp;     localStorage.removeItem('access\_token');

&nbsp;     localStorage.removeItem('user');

&nbsp;     // Only redirect if not already on login page

&nbsp;     if (window.location.pathname !== '/login') {

&nbsp;       window.location.href = '/login';

&nbsp;     }

&nbsp;   }

&nbsp;   return Promise.reject(error);

&nbsp; }

);



export default client;



frontend/src/api/auth.js



javascript

import client from './client';



export async function login(username, password) {

&nbsp; // OAuth2 password flow uses form-urlencoded

&nbsp; const params = new URLSearchParams();

&nbsp; params.append('username', username);

&nbsp; params.append('password', password);



&nbsp; const response = await client.post('/auth/login', params, {

&nbsp;   headers: { 'Content-Type': 'application/x-www-form-urlencoded' },

&nbsp; });

&nbsp; return response.data; // Token

}



export async function getMe() {

&nbsp; const response = await client.get('/auth/me');

&nbsp; return response.data; // UserResponse

}



export async function registerUser(userData) {

&nbsp; const response = await client.post('/auth/register', userData);

&nbsp; return response.data; // UserResponse

}



export async function updateUser(userId, userData) {

&nbsp; const response = await client.put(/auth/users/${userId}, userData);

&nbsp; return response.data; // UserResponse

}



export async function listUsers(params = {}) {

&nbsp; const response = await client.get('/auth/users', { params });

&nbsp; return response.data; // List\[UserResponse]

}



frontend/src/api/runs.js



javascript

import client from './client';



export async function createRun(runData) {

&nbsp; const response = await client.post('/pipeline/run', runData);

&nbsp; return response.data;

}



export async function listRuns(params = {}) {

&nbsp; const response = await client.get('/runs', { params });

&nbsp; return response.data;

}



export async function getRun(runId) {

&nbsp; const response = await client.get(/runs/${runId});

&nbsp; return response.data;

}



export async function getRunSummary(runId) {

&nbsp; const response = await client.get(/summary/${runId});

&nbsp; return response.data;

}



export async function listNotebookOutputs(runId) {

&nbsp; const response = await client.get(/runs/${runId}/notebook-outputs);

&nbsp; return response.data;

}



export async function downloadNotebookOutput(runId, outputKey) {

&nbsp; const response = await client.get(

&nbsp;   /runs/${runId}/notebook-outputs/${outputKey}/download,

&nbsp;   { responseType: 'blob' }

&nbsp; );

&nbsp; return response;

}



export async function listRunArchive(runId) {

&nbsp; const response = await client.get(/runs/${runId}/archive);

&nbsp; return response.data;

}



export async function downloadArchiveFile(runId, path) {

&nbsp; const response = await client.get(

&nbsp;   /runs/${runId}/archive/download,

&nbsp;   { params: { path }, responseType: 'blob' }

&nbsp; );

&nbsp; return response;

}



export async function getSalesTeams() {

&nbsp; const response = await client.get('/sales-teams');

&nbsp; return response.data;

}



export async function getConfig() {

&nbsp; const response = await client.get('/config');

&nbsp; return response.data;

}



frontend/src/api/exceptions.js



javascript

import client from './client';



export async function listExceptions(params = {}) {

&nbsp; const response = await client.get('/exceptions', { params });

&nbsp; return response.data;

}



export async function exportExceptions(params = {}) {

&nbsp; const response = await client.get('/exceptions/export', {

&nbsp;   params,

&nbsp;   responseType: 'blob',

&nbsp; });

&nbsp; return response;

}



frontend/src/api/loans.js



javascript

import client from './client';



export async function listLoans(params = {}) {

&nbsp; const response = await client.get('/loans', { params });

&nbsp; return response.data;

}



frontend/src/api/files.js



javascript

import client from './client';



export async function listFiles(params = {}) {

&nbsp; const response = await client.get('/files/list', { params });

&nbsp; return response.data;

}



export async function uploadFile(file, path = '', area = 'inputs') {

&nbsp; const formData = new FormData();

&nbsp; formData.append('file', file);

&nbsp; const response = await client.post('/files/upload', formData, {

&nbsp;   params: { path, area },

&nbsp;   headers: { 'Content-Type': 'multipart/form-data' },

&nbsp;   // Track upload progress

&nbsp;   onUploadProgress: (progressEvent) => {

&nbsp;     const pct = Math.round((progressEvent.loaded \* 100) / progressEvent.total);

&nbsp;     // Can be wired to a progress callback

&nbsp;     console.log(Upload progress: ${pct}%);

&nbsp;   },

&nbsp; });

&nbsp; return response.data;

}



export async function downloadFile(filePath, area = 'inputs') {

&nbsp; const response = await client.get(/files/download/${filePath}, {

&nbsp;   params: { area },

&nbsp;   responseType: 'blob',

&nbsp; });

&nbsp; return response;

}



export async function getFileUrl(filePath, area = 'inputs', expiresIn = 3600) {

&nbsp; const response = await client.get(/files/url/${filePath}, {

&nbsp;   params: { area, expires\_in: expiresIn },

&nbsp; });

&nbsp; return response.data;

}



export async function deleteFile(filePath, area = 'inputs') {

&nbsp; const response = await client.delete(/files/${filePath}, {

&nbsp;   params: { area },

&nbsp; });

&nbsp; return response.data;

}



export async function createDirectory(path, area = 'inputs') {

&nbsp; const response = await client.post('/files/mkdir', null, {

&nbsp;   params: { path, area },

&nbsp; });

&nbsp; return response.data;

}





Auth Context \& Hook



frontend/src/context/AuthContext.jsx



jsx

/

• Authentication context provider.

• Manages JWT token storage, user state, and auth operations.

• Wraps the entire app to provide auth state to all components.

&nbsp;\*/

import { createContext, useState, useEffect, useCallback } from 'react';

import { login as apiLogin, getMe } from '../api/auth';



export const AuthContext = createContext(null);



export function AuthProvider({ children }) {

&nbsp; const \[user, setUser] = useState(null);

&nbsp; const \[loading, setLoading] = useState(true);

&nbsp; const \[error, setError] = useState(null);



&nbsp; // Check for existing token on mount

&nbsp; useEffect(() => {

&nbsp;   const token = localStorage.getItem('access\_token');

&nbsp;   if (token) {

&nbsp;     getMe()

&nbsp;       .then((userData) => {

&nbsp;         setUser(userData);

&nbsp;       })

&nbsp;       .catch(() => {

&nbsp;         // Token is invalid or expired

&nbsp;         localStorage.removeItem('access\_token');

&nbsp;         localStorage.removeItem('user');

&nbsp;         setUser(null);

&nbsp;       })

&nbsp;       .finally(() => setLoading(false));

&nbsp;   } else {

&nbsp;     setLoading(false);

&nbsp;   }

&nbsp; }, \[]);



&nbsp; const login = useCallback(async (username, password) => {

&nbsp;   setError(null);

&nbsp;   try {

&nbsp;     const tokenData = await apiLogin(username, password);

&nbsp;     localStorage.setItem('access\_token', tokenData.access\_token);

&nbsp;     localStorage.setItem('user', JSON.stringify(tokenData.user));

&nbsp;     setUser(tokenData.user);

&nbsp;     return tokenData;

&nbsp;   } catch (err) {

&nbsp;     const message = err.response?.data?.detail || 'Login failed';

&nbsp;     setError(message);

&nbsp;     throw err;

&nbsp;   }

&nbsp; }, \[]);



&nbsp; const logout = useCallback(() => {

&nbsp;   localStorage.removeItem('access\_token');

&nbsp;   localStorage.removeItem('user');

&nbsp;   setUser(null);

&nbsp;   window.location.href = '/login';

&nbsp; }, \[]);



&nbsp; const isAdmin = user?.role === 'admin';

&nbsp; const isAuthenticated = !!user;



&nbsp; return (

&nbsp;   <AuthContext.Provider value={{

&nbsp;     user, loading, error, login, logout, isAdmin, isAuthenticated,

&nbsp;   }}>

&nbsp;     {children}

&nbsp;   </AuthContext.Provider>

&nbsp; );

}



frontend/src/hooks/useAuth.js



javascript

import { useContext } from 'react';

import { AuthContext } from '../context/AuthContext';



export function useAuth() {

&nbsp; const context = useContext(AuthContext);

&nbsp; if (!context) {

&nbsp;   throw new Error('useAuth must be used within an AuthProvider');

&nbsp; }

&nbsp; return context;

}





Utility Hooks



frontend/src/hooks/useApi.js



javascript

/

• Generic API call hook with loading, error, and data state.

• \* Usage:

• const { data, loading, error, execute } = useApi(listRuns);

• useEffect(() => { execute({ status: 'completed' }); }, \[]);

&nbsp;\*/

import { useState, useCallback } from 'react';



export function useApi(apiFn) {

&nbsp; const \[data, setData] = useState(null);

&nbsp; const \[loading, setLoading] = useState(false);

&nbsp; const \[error, setError] = useState(null);



&nbsp; const execute = useCallback(async (...args) => {

&nbsp;   setLoading(true);

&nbsp;   setError(null);

&nbsp;   try {

&nbsp;     const result = await apiFn(...args);

&nbsp;     setData(result);

&nbsp;     return result;

&nbsp;   } catch (err) {

&nbsp;     const message = err.response?.data?.detail || err.message || 'An error occurred';

&nbsp;     setError(message);

&nbsp;     throw err;

&nbsp;   } finally {

&nbsp;     setLoading(false);

&nbsp;   }

&nbsp; }, \[apiFn]);



&nbsp; const reset = useCallback(() => {

&nbsp;   setData(null);

&nbsp;   setError(null);

&nbsp;   setLoading(false);

&nbsp; }, \[]);



&nbsp; return { data, loading, error, execute, reset };

}



frontend/src/hooks/usePagination.js



javascript

import { useState, useCallback } from 'react';



export function usePagination(initialLimit = 25) {

&nbsp; const \[skip, setSkip] = useState(0);

&nbsp; const \[limit] = useState(initialLimit);



&nbsp; const nextPage = useCallback(() => setSkip((s) => s + limit), \[limit]);

&nbsp; const prevPage = useCallback(() => setSkip((s) => Math.max(0, s - limit)), \[limit]);

&nbsp; const goToPage = useCallback((page) => setSkip(page \* limit), \[limit]);

&nbsp; const resetPage = useCallback(() => setSkip(0), \[]);



&nbsp; const currentPage = Math.floor(skip / limit);



&nbsp; return { skip, limit, currentPage, nextPage, prevPage, goToPage, resetPage };

}



frontend/src/utils/format.js



javascript

/

• Formatting utilities for numbers, dates, and currencies.

&nbsp;\*/



export function formatCurrency(value) {

&nbsp; if (value == null) return '—';

&nbsp; return new Intl.NumberFormat('en-US', {

&nbsp;   style: 'currency', currency: 'USD',

&nbsp;   minimumFractionDigits: 0, maximumFractionDigits: 0,

&nbsp; }).format(value);

}



export function formatNumber(value, decimals = 0) {

&nbsp; if (value == null) return '—';

&nbsp; return new Intl.NumberFormat('en-US', {

&nbsp;   minimumFractionDigits: decimals,

&nbsp;   maximumFractionDigits: decimals,

&nbsp; }).format(value);

}



export function formatPercent(value, decimals = 2) {

&nbsp; if (value == null) return '—';

&nbsp; return ${value.toFixed(decimals)}%;

}



export function formatDate(isoString) {

&nbsp; if (!isoString) return '—';

&nbsp; return new Date(isoString).toLocaleDateString('en-US', {

&nbsp;   year: 'numeric', month: 'short', day: 'numeric',

&nbsp; });

}



export function formatDateTime(isoString) {

&nbsp; if (!isoString) return '—';

&nbsp; return new Date(isoString).toLocaleString('en-US', {

&nbsp;   year: 'numeric', month: 'short', day: 'numeric',

&nbsp;   hour: '2-digit', minute: '2-digit',

&nbsp; });

}



export function formatFileSize(bytes) {

&nbsp; if (bytes === 0) return '0 B';

&nbsp; const units = \['B', 'KB', 'MB', 'GB'];

&nbsp; const i = Math.floor(Math.log(bytes) / Math.log(1024));

&nbsp; return ${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units\[i]};

}



export function formatDuration(startIso, endIso) {

&nbsp; if (!startIso || !endIso) return '—';

&nbsp; const ms = new Date(endIso) - new Date(startIso);

&nbsp; const seconds = Math.floor(ms / 1000);

&nbsp; if (seconds < 60) return ${seconds}s;

&nbsp; const minutes = Math.floor(seconds / 60);

&nbsp; const remainingSeconds = seconds % 60;

&nbsp; return ${minutes}m ${remainingSeconds}s;

}



/

• Trigger a browser file download from a blob response.

&nbsp;\*/

export function downloadBlob(response, defaultFilename = 'download') {

&nbsp; const contentDisposition = response.headers\['content-disposition'];

&nbsp; let filename = defaultFilename;

&nbsp; if (contentDisposition) {

&nbsp;   const match = contentDisposition.match(/filename="?(\[^"]+)"?/);

&nbsp;   if (match) filename = match\[1];

&nbsp; }

&nbsp; const url = window.URL.createObjectURL(new Blob(\[response.data]));

&nbsp; const link = document.createElement('a');

&nbsp; link.href = url;

&nbsp; link.download = filename;

&nbsp; document.body.appendChild(link);

&nbsp; link.click();

&nbsp; link.remove();

&nbsp; window.URL.revokeObjectURL(url);

}





Reusable Components



Generate complete implementations for each component:



frontend/src/components/ProtectedRoute.jsx

• If loading → show LoadingSpinner

• If not isAuthenticated → Navigate to /login

• If requireAdmin prop and not isAdmin → show "Access denied" message

• Otherwise render <Outlet /> or children



frontend/src/components/StatusBadge.jsx

• Accepts status prop: "pending" | "running" | "completed" | "failed"

• Renders colored badge with text

• Colors: pending=gray, running=blue+pulse animation, completed=green, failed=red



frontend/src/components/Pagination.jsx

• Props: currentPage, totalItems, limit, onPageChange

• Shows: "Showing X-Y of Z" text, Previous/Next buttons, page number

• Disables Previous on first page, Next when no more items



frontend/src/components/DataTable.jsx

• Props: columns (array of {key, label, render?, sortable?}), data, onSort, sortKey, sortDir

• Renders table with sortable column headers (click to toggle asc/desc)

• Alternating row colors, hover highlight

• Empty state message when no data

• render function on columns for custom cell rendering



frontend/src/components/Modal.jsx

• Props: isOpen, onClose, title, children, footer

• Overlay with centered dialog, close button, escape key to close

• Click outside to close

• Focus trap within modal when open



frontend/src/components/LoadingSpinner.jsx

• Centered spinning indicator

• Optional message prop for text below spinner



frontend/src/components/ErrorMessage.jsx

• Props: message, onRetry (optional)

• Red alert box with error icon, message text, and optional "Retry" button



frontend/src/components/FileUploader.jsx

• Drag-and-drop zone for file uploads

• Props: onUpload(file), accept (file types), area, path

• Shows file name and size after selection

• Upload progress bar

• Success/error feedback

• Allowed extensions: .csv, .xlsx, .xls, .json, .txt, .pdf, .zip





Page Implementations



frontend/src/pages/LoginPage.jsx



Full-screen centered login form:

• Username and password fields with labels

• "Sign In" button with loading state

• Error message display for invalid credentials

• Redirect to /dashboard on successful login

• If already authenticated, redirect to /dashboard

• Clean, professional styling

• Enter key submits form



frontend/src/pages/DashboardPage.jsx



Pipeline runs dashboard with two sections:



Header section:

• Page title "Pipeline Runs"

• "New Run" button (opens modal)

• Filter controls: status dropdown (all/pending/running/completed/failed),

&nbsp; weekday dropdown (all/Mon-Sun)



New Run Modal:

• Form fields: Purchase Date (text input), IRR Target (number input, default 8.05),

&nbsp; Folder (text input, optional)

• Submit triggers POST /api/pipeline/run

• Show loading spinner during pipeline execution

• On success, close modal and refresh run list

• On error, show error message in modal



Runs Table:

• Columns: Status (StatusBadge), Run ID (link to detail), Purchase Date,

&nbsp; Total Loans (formatted number), Total Balance (formatted currency),

&nbsp; Exceptions, Duration, Created At

• Sortable by any column

• Pagination (25 per page)

• Click row → navigate to /runs/{run\_id}

• Auto-refresh every 10 seconds if any run has status "running"



frontend/src/pages/RunDetailPage.jsx



Detailed view of a single pipeline run with tabbed sections:



Header:

• Back button (← Runs)

• Run ID and StatusBadge

• Key metrics row: Total Loans, Total Balance, Exceptions, Duration



Tabs:

1\. Summary (default tab)

• Fetch GET /api/summary/{run\_id}

• Display eligibility checks as a summary card grid:

• Total Loans, Eligible, Rejected, Projected (as metric cards)

• Exceptions by Type (simple bar list or table)

• Exceptions by Severity (hard count, soft count)

2\. Loans

• Fetch GET /api/loans?run\_id={run\_id}

• Disposition filter tabs: All | To Purchase | Projected | Rejected

• DataTable with loan fields from loan\_data

• Pagination

3\. Exceptions

• Fetch GET /api/exceptions?run\_id={run\_id}

• Filter by severity (all/hard/soft) and type

• DataTable: Loan Number, Type, Category, Severity, Message, Rejection Criteria

• Pagination

• "Export CSV" and "Export Excel" buttons

4\. Outputs

• Fetch GET /api/runs/{run\_id}/notebook-outputs

• List of 4 output files with name, size, download button

• Each download button calls the download endpoint and triggers browser download

5\. Archive

• Fetch GET /api/runs/{run\_id}/archive

• Two sections: Input Files, Output Files

• Each file has name, size, download button



frontend/src/pages/ExceptionsPage.jsx



Global exception browser (across all runs):

• Filters: Run ID (dropdown of completed runs), Exception Type (dropdown),

&nbsp; Severity (all/hard/soft), Rejection Criteria (text search)

• DataTable: Run ID (link), Loan Number, Type, Category, Severity,

&nbsp; Message, Rejection Criteria, Created At

• Pagination (25 per page)

• Export buttons: "Export CSV", "Export Excel"

• Trigger GET /api/exceptions/export?format=csv (or xlsx) with current filters

• Browser downloads the file



frontend/src/pages/FilesPage.jsx



File manager with three-panel layout:



Top bar:

• Area selector tabs: Inputs | Outputs | Output Share

• Current path breadcrumb (clickable segments)

• "Upload File" button, "New Folder" button



File list:

• DataTable: Name (icon for file/folder), Size, Last Modified

• Click folder → navigate into it (update path)

• Click file → show action menu (Download, Get URL, Delete)

• Sort by name, size, or date



Upload:

• FileUploader component appears when "Upload File" clicked

• Uploads to current path in current area

• Refreshes file list on success



Actions:

• Download: triggers browser download via GET /api/files/download/{path}

• Get URL: shows modal with presigned URL (or local path) and copy button

• Delete: confirmation modal → DELETE /api/files/{path} → refresh list

• New Folder: prompt for folder name → POST /api/files/mkdir → refresh list



frontend/src/pages/UsersPage.jsx



Admin-only user management:

• If not admin, show "Access restricted to administrators"

• "Add User" button (opens modal)



Users table:

• Columns: Username, Email, Full Name, Role (colored badge), Sales Team,

&nbsp; Active (green/red indicator), Actions

• Actions: Edit (opens modal), Toggle Active



Add/Edit User Modal:

• Form fields: Email, Username, Full Name, Password (required for new, optional for edit),

&nbsp; Role (dropdown: admin/analyst/sales\_team), Sales Team (dropdown, loaded from

&nbsp; GET /api/sales-teams), Active (checkbox)

• Validation: email format, username 3-50 chars, password 8+ chars

• Submit: POST /auth/register (new) or PUT /auth/users/{id} (edit)

• Success → close modal, refresh table

• Error → show message in modal





Routing (frontend/src/App.jsx)



jsx

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { AuthProvider } from './context/AuthContext';

import ProtectedRoute from './components/ProtectedRoute';

import Layout from './components/Layout';

import LoginPage from './pages/LoginPage';

import DashboardPage from './pages/DashboardPage';

import RunDetailPage from './pages/RunDetailPage';

import ExceptionsPage from './pages/ExceptionsPage';

import FilesPage from './pages/FilesPage';

import UsersPage from './pages/UsersPage';



export default function App() {

&nbsp; return (

&nbsp;   <BrowserRouter>

&nbsp;     <AuthProvider>

&nbsp;       <Routes>

&nbsp;         {/ Public route /}

&nbsp;         <Route path="/login" element={<LoginPage />} />



&nbsp;         {/ Protected routes /}

&nbsp;         <Route element={<ProtectedRoute />}>

&nbsp;           <Route element={<Layout />}>

&nbsp;             <Route path="/dashboard" element={<DashboardPage />} />

&nbsp;             <Route path="/runs/:runId" element={<RunDetailPage />} />

&nbsp;             <Route path="/exceptions" element={<ExceptionsPage />} />

&nbsp;             <Route path="/files" element={<FilesPage />} />

&nbsp;             <Route path="/users" element={<ProtectedRoute requireAdmin><UsersPage /></ProtectedRoute>} />

&nbsp;           </Route>

&nbsp;         </Route>



&nbsp;         {/ Default redirect /}

&nbsp;         <Route path="\*" element={<Navigate to="/dashboard" replace />} />

&nbsp;       </Routes>

&nbsp;     </AuthProvider>

&nbsp;   </BrowserRouter>

&nbsp; );

}





Layout Component (frontend/src/components/Layout.jsx)



The app shell with sidebar navigation and content area:





┌─────────────────────────────────────────────────────────┐

│ ┌──────────┐ ┌────────────────────────────────────────┐ │

│ │          │ │ Header: Page title     User ▼ | Logout │ │

│ │ SIDEBAR  │ ├────────────────────────────────────────┤ │

│ │          │ │                                        │ │

│ │ ◉ Runs   │ │                                        │ │

│ │ ○ Except │ │         CONTENT AREA                   │ │

│ │ ○ Files  │ │         (Outlet)                       │ │

│ │ ○ Users  │ │                                        │ │

│ │          │ │                                        │ │

│ │──────────│ │                                        │ │

│ │ v1.0.0   │ │                                        │ │

│ └──────────┘ └────────────────────────────────────────┘ │

└─────────────────────────────────────────────────────────┘



Sidebar navigation items:

• Pipeline Runs → /dashboard (icon: play/list)

• Exceptions → /exceptions (icon: warning)

• Files → /files (icon: folder)

• Users → /users (icon: people) — only visible for admin role



Active route highlighted in sidebar.

User info in header: username, role badge.

Logout button in header.



Content area renders <Outlet /> from React Router.





Validation Criteria for Phase 4



After implementation, ALL must pass:

1\. npm install completes without errors

2\. npm run build produces frontend/dist/ with index.html and assets/

3\. npm run dev starts Vite on port 5173 without errors

4\. All page components render without React errors (no console.error)

5\. LoginPage: form submits, stores token, redirects to /dashboard

6\. DashboardPage: loads and displays runs from API

7\. DashboardPage: "New Run" modal creates a pipeline run

8\. RunDetailPage: loads run data with all 5 tabs functional

9\. RunDetailPage: download buttons trigger file downloads

10\. ExceptionsPage: loads exceptions with working filters and export

11\. FilesPage: lists files, navigates directories, uploads and downloads work

12\. UsersPage: admin can list, create, and edit users

13\. UsersPage: non-admin sees access denied message

14\. Auth flow: 401 response redirects to login page

15\. Responsive: layout adapts below 768px width

16\. No hardcoded API URLs (all use /api proxy)

17\. No console errors or warnings in browser

18\. All API modules import and export correctly:

&nbsp;     node -e "import('./frontend/src/api/client.js')"



Run validation:



bash

cd frontend

npm install

npm run build

Verify dist/ output

ls dist/index.html dist/assets/.js dist/assets/.css





Chunking Guide (if prompt exceeds context limits)



| Chunk | File(s) | Focus |

|-------|---------|-------|

| 4a | global.css, format.js | Design system + utilities |

| 4b | client.js, auth.js, runs.js, exceptions.js, loans.js, files.js | API layer |

| 4c | AuthContext.jsx, useAuth.js, useApi.js, usePagination.js | State management |

| 4d | All components in components/ | Reusable UI components |

| 4e | App.jsx, Layout.jsx, ProtectedRoute.jsx | Routing + shell |

| 4f | LoginPage.jsx, DashboardPage.jsx | Auth + main page |

| 4g | RunDetailPage.jsx | Run detail with 5 tabs |

| 4h | ExceptionsPage.jsx, FilesPage.jsx, UsersPage.jsx | Remaining pages |



Prepend API schema reference (the TypeScript interfaces section above) to each chunk.



