import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { observer } from 'mobx-react-lite';
import { authStore } from '../../store/authStore';
import { getStoredToken } from '../../api/client';
import { Spinner } from '../ui/spinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = observer(({ children }) => {
  const location = useLocation();
  const hasToken = getStoredToken();
  const isRestoring = hasToken && !authStore.user;

  useEffect(() => {
    if (hasToken && !authStore.user) {
      authStore.fetchMe();
    }
  }, [hasToken]);

  if (authStore.isAuthenticated) {
    return <>{children}</>;
  }
  if (isRestoring) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <Spinner className='size-5' />
      </div>
    );
  }
  return <Navigate to="/login" state={{ from: location }} replace />;
});

export default ProtectedRoute;
