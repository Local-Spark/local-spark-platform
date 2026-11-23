// Absolute-time helpers. Text endpoints are inclusive; photo handoffs are half-open.
(() => {
  const textVisible = (ms, start, end) => ms >= start && ms <= end;
  const photoVisible = (ms, start, end, reelEnd) => ms >= start && (ms < end || ms === reelEnd && end === reelEnd);
  const outgoingOpacity = (ms, start, end) => 1 - Math.max(0, Math.min(1, (ms - start) / (end - start)));
  Object.defineProperty(window, 'PhotoTimingV1', {
    value: Object.freeze({textVisible, photoVisible, outgoingOpacity}), writable: false, configurable: false,
  });
})();
