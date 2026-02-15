-- Add missing fields to incidents table for metrics

ALTER TABLE incidents ADD COLUMN assignee TEXT;
ALTER TABLE incidents ADD COLUMN jira_project TEXT;
ALTER TABLE incidents ADD COLUMN status TEXT DEFAULT 'open';
