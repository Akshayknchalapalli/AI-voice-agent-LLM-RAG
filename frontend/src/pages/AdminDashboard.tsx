import React, { useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  CircularProgress,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from 'react-query';
import axios from 'axios';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ width: '100%' }}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const AdminDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  // Fetch analytics data
  const { data: analytics, isLoading: loadingAnalytics } = useQuery(
    'analytics',
    async () => {
      const response = await axios.get('/api/admin/analytics');
      return response.data;
    },
    {
      refetchInterval: 60000 // Refresh every minute
    }
  );

  // Fetch recent conversations
  const { data: conversations, isLoading: loadingConversations } = useQuery(
    'conversations',
    async () => {
      const response = await axios.get('/api/admin/conversations');
      return response.data;
    },
    {
      refetchInterval: 30000 // Refresh every 30 seconds
    }
  );

  return (
    <Container maxWidth="xl">
      <Box py={4}>
        <Typography variant="h4" gutterBottom>
          Admin Dashboard
        </Typography>

        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          sx={{ mb: 3 }}
        >
          <Tab label="Overview" />
          <Tab label="Conversations" />
          <Tab label="Properties" />
          <Tab label="System Health" />
        </Tabs>

        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {/* Key Metrics */}
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6">Active Sessions</Typography>
                <Typography variant="h3">
                  {loadingAnalytics ? (
                    <CircularProgress size={30} />
                  ) : (
                    analytics?.activeSessions || 0
                  )}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6">Today's Inquiries</Typography>
                <Typography variant="h3">
                  {loadingAnalytics ? (
                    <CircularProgress size={30} />
                  ) : (
                    analytics?.dailyInquiries || 0
                  )}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6">Conversion Rate</Typography>
                <Typography variant="h3">
                  {loadingAnalytics ? (
                    <CircularProgress size={30} />
                  ) : (
                    `${(analytics?.conversionRate || 0).toFixed(1)}%`
                  )}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6">Avg. Response Time</Typography>
                <Typography variant="h3">
                  {loadingAnalytics ? (
                    <CircularProgress size={30} />
                  ) : (
                    `${(analytics?.avgResponseTime || 0).toFixed(1)}s`
                  )}
                </Typography>
              </Paper>
            </Grid>

            {/* Activity Chart */}
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Activity Overview
                </Typography>
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={analytics?.activityData || []}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="conversations"
                        stroke="#8884d8"
                        name="Conversations"
                      />
                      <Line
                        type="monotone"
                        dataKey="inquiries"
                        stroke="#82ca9d"
                        name="Inquiries"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Conversations Tab */}
        <TabPanel value={tabValue} index={1}>
          <Paper>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Session ID</TableCell>
                  <TableCell>Start Time</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Properties Discussed</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loadingConversations ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : (
                  conversations?.map((conv: any) => (
                    <TableRow key={conv.sessionId}>
                      <TableCell>{conv.sessionId}</TableCell>
                      <TableCell>{new Date(conv.startTime).toLocaleString()}</TableCell>
                      <TableCell>{conv.duration}m</TableCell>
                      <TableCell>{conv.propertiesDiscussed}</TableCell>
                      <TableCell>{conv.status}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Paper>
        </TabPanel>

        {/* Additional tabs implementation... */}
      </Box>
    </Container>
  );
};

export default AdminDashboard;
