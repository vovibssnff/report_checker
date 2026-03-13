import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppContainer from './components/AppContainer/AppContainer';
import ChatArea from './components/ChatArea/ChatArea';
import SidebarHeader from './components/SidebarHeader/SidebarHeader';
import ProtectedRoute from './components/ProtectedRoute/ProtectedRoute';
import AuthPage from './pages/AuthPage';
import { authStore } from './store/authStore';

function TicketsApp() {
  useEffect(() => {
    authStore.fetchMe();
  }, []);
  return (
    <AppContainer>
      <div className="fixed top-0 left-0 right-0 z-50 bg-linear-to-b from-white to-transparent">
        <SidebarHeader />
      </div>
      <div className="flex-1 min-h-0 pt-[72px] overflow-hidden">
        <ChatArea />
      </div>
    </AppContainer>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route path="/register" element={<AuthPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <TicketsApp />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
