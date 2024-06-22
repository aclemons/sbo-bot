const config = {
  proseWrap: 'always',
  tabWidth: 2,
  singleQuote: true,
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,
  plugins: [require.resolve('@trivago/prettier-plugin-sort-imports')],
};

module.exports = config;
