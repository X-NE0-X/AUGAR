import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle, Info, CheckCircle } from 'lucide-react';

type ToastType = 'info' | 'error' | 'success';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 1000, display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="glass"
              style={{
                padding: '16px 20px',
                borderRadius: '16px',
                minWidth: '300px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
                borderLeft: `4px solid ${
                  toast.type === 'error' ? 'var(--unfavorable)' : 
                  toast.type === 'success' ? 'var(--favorable)' : 
                  'var(--amber)'
                }`
              }}
            >
              {toast.type === 'error' && <AlertCircle size={20} color="var(--unfavorable)" />}
              {toast.type === 'success' && <CheckCircle size={20} color="var(--favorable)" />}
              {toast.type === 'info' && <Info size={20} color="var(--amber)" />}
              
              <div style={{ flex: 1, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{toast.message}</div>
              
              <button 
                onClick={() => removeToast(toast.id)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={16} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within a ToastProvider');
  return context;
};
