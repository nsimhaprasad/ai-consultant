import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';

// Layout Components
import Layout from './components/layout/Layout';

// Pages
import HomePage from './pages/HomePage';
import HostedPage from './pages/HostedPage';
import OnPremisePage from './pages/OnPremisePage';
import PricingPage from './pages/PricingPage';
import LicensePage from './pages/LicensePage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/hosted" element={<HostedPage />} />
          <Route path="/on-premise" element={<OnPremisePage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/terms" element={<LicensePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;