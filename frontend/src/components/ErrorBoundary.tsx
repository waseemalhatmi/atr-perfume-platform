import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { logger } from '@/lib/logger';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logger.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background text-center p-6">
          <div className="glass rounded-3xl p-10 max-w-lg w-full flex flex-col items-center gap-6">
            <div className="w-20 h-20 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center">
              <AlertTriangle size={40} />
            </div>
            <div>
              <h2 className="text-2xl font-bold mb-2">عذراً، حدث خطأ غير متوقع!</h2>
              <p className="text-muted-foreground">لقد واجهنا مشكلة فنية. يرجى إعادة تحميل الصفحة.</p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="btn-gold w-full py-4"
            >
              إعادة تحميل الصفحة
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
