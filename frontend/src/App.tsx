import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Questions from './pages/Questions';
import QuestionForm from './pages/QuestionForm';
import QuestionDetail from './pages/QuestionDetail';
import GradePaper from './pages/GradePaper';
import ScorePreview from './pages/ScorePreview';
import About from './pages/About';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="grade-paper" element={<GradePaper />} />
              <Route path="questions" element={<Questions />} />
              <Route path="questions/new" element={<QuestionForm />} />
              <Route path="questions/:id" element={<QuestionDetail />} />
              <Route path="questions/:id/edit" element={<QuestionForm />} />
              <Route path="score-preview" element={<ScorePreview />} />
              <Route path="about" element={<About />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
