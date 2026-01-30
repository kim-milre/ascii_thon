import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const AdminRoute = ({ children }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>로딩 중...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin()) {
    return (
      <div className="error-container">
        <h2>접근 권한이 없습니다</h2>
        <p>이 페이지는 관리자만 접근할 수 있습니다.</p>
        <button 
          onClick={() => window.history.back()}
          className="btn btn-primary"
        >
          이전 페이지로 돌아가기
        </button>
      </div>
    );
  }

  return children;
};

export default AdminRoute;
