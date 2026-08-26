import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useApp } from '../../context/AppContext';

export const ProtectedRoute = ({ allowedRole }) => {
  const { isAuthenticated, userRole } = useApp();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && userRole !== allowedRole) {
    return <Navigate to={userRole === 'doctor' ? '/doctor' : '/dashboard'} replace />;
  }

  return <Outlet />;
};
