import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { observer } from 'mobx-react-lite';
import { authStore } from '../../store/authStore';
import { Spinner } from '../ui/spinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRouteInner = ({ children }: ProtectedRouteProps) => {
  const location = useLocation();

  useEffect(() => {
    if (!authStore.user && !authStore.loading) authStore.fetchMe();
    // Intentionally run once on mount to restore session.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (authStore.user) return <>{children}</>;
  if (authStore.loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <Spinner className='size-5' />
      </div>
    );
  }
  return <Navigate to="/login" state={{ from: location }} replace />;
};

export default observer(ProtectedRouteInner);
