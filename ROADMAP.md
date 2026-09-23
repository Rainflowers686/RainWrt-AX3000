# Roadmap

Near-term priorities:

- Validate additional CR880X hardware before making broader support claims.
- Add a controlled wired-to-Wi-Fi throughput test, especially for QCN6122.
- Use a controlled WireGuard benchmark endpoint before publishing device-limit
  throughput claims.
- Extend long-duration stability observation beyond the current bounded test.
- Forward-port the device layer to later ImmortalWrt stable releases with
  explicit layout and package-feed review.
- Continue NSS compatibility research; do not treat qca_nss_dp alone as
  complete acceleration.
- Keep any overclock work experimental and separate; current hardware tests
  validate only the stock 1.008 GHz operating point.
- Keep prebuilt firmware and package-feed distribution blocked until
  vendor-origin redistribution terms for device-specific board data are
  established; continue auditing public refs as source evolves.

No roadmap item implies a current firmware feature or test result.
