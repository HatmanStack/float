module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'chore',
        'docs',
        'test',
        'ci',
        'refactor',
        'perf',
        'style',
        'build',
        'revert',
      ],
    ],
    'scope-enum': [
      1,
      'always',
      ['frontend', 'backend'],
    ],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [1, 'always', 100],
  },
};
