const fs = require('fs').promises;
const path = require('path');

class CursorLogger {
  constructor() {
    this.SPECSTORY_DIR = path.join(process.cwd(), 'specstory');
    this.logData = {
      conversation_history: []
    };
  }

  async captureConversationHistory() {
    try {
      const files = await fs.readdir(this.SPECSTORY_DIR);
      const mdFiles = files.filter(f => f.endsWith('.md'));
      
      // Sort files by modification time (most recent first)
      const fileStats = await Promise.all(mdFiles.map(async f => {
        const stats = await fs.stat(path.join(this.SPECSTORY_DIR, f));
        return { file: f, mtime: stats.mtime };
      }));
      fileStats.sort((a, b) => b.mtime - a.mtime);

      // Read most recent file
      if (fileStats.length > 0) {
        const mostRecentFile = fileStats[0].file;
        const content = await fs.readFile(path.join(this.SPECSTORY_DIR, mostRecentFile), 'utf8');
        
        // Split content into lines and process messages
        const lines = content.split('\n');
        let currentRole = null;
        let currentContent = [];
        const messages = [];

        for (let line of lines) {
          if (line.includes('_**User**_')) {
            if (currentRole && currentContent.length > 0) {
              messages.push({
                role: currentRole,
                content: currentContent.join('\n').trim()
              });
            }
            currentRole = 'user';
            currentContent = [];
          } else if (line.includes('_**Assistant**_')) {
            if (currentRole && currentContent.length > 0) {
              messages.push({
                role: currentRole,
                content: currentContent.join('\n').trim()
              });
            }
            currentRole = 'assistant';
            currentContent = [];
          } else if (currentRole && !line.includes('---')) {
            currentContent.push(line);
          }
        }

        // Add final message if exists
        if (currentRole && currentContent.length > 0) {
          messages.push({
            role: currentRole,
            content: currentContent.join('\n').trim()
          });
        }

        this.logData.conversation_history = messages;
        console.log(`Found ${messages.length} messages in recent conversation history`);
      }
    } catch (error) {
      console.error('Error reading SpecStory history:', error);
    }
  }
}

module.exports = CursorLogger; 