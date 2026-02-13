hexo.extend.injector.register('head_end', () => `
<link rel="stylesheet" href="/agreement/agreement.css">
`);

hexo.extend.injector.register('body_end', () => `
<div id="agreement-root"></div>
<script src="/agreement/agreement.js"></script>
`);
