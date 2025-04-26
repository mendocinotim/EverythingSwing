// COMPLETE REPLACEMENT FOR core/orchestrator/project-orchestrator.js
require('dotenv').config();
const { Perplexity } = require('perplexity-api');
const { cursorHook } = require('@cursor-so/agent-hook');

class ProjectOrchestrator {
  constructor() {
    this.pxl = new Perplexity(process.env.PERPLEXITY_API_KEY);
    this.actions = [];
    
    cursorHook.init({
      logPath: process.env.CURSOR_AGENT_HOOK_PATH,
      onAction: (action) => this.handleAction(action)
    });
  }

  handleAction(action) {
    this.actions.push(action);
    this.generateReport();
  }

  async generateReport() {
    const report = await this.pxl.deepResearch({
      query: `Cursor Actions: ${JSON.stringify(this.actions)}\nRecommend next steps.`
    });
    
    console.log('Perplexity Recommendation:', report);
    cursorHook.displayNotification(report.summary);
  }
}

new ProjectOrchestrator();
