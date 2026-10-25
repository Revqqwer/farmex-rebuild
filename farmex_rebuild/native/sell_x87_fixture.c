/* Own isolated arithmetic oracle. No DLL loading, target process, game or IO except stdout. */
#include <stdio.h>
#include <stdint.h>
#include "sell_x87_cases.h"

static uint64_t source_shape(uint64_t raw, unsigned short control, unsigned short *after) {
    uint64_t result, coefficient=0x3f9eb851eb851eb8ULL;
    unsigned short saved, truncation=(unsigned short)(control|0x0c01), restored;
    __asm__ __volatile__("fnstcw %0" : "=m"(saved));
    __asm__ __volatile__(
        "fninit\n\t" /* Fixture forces empty clean stack before the source-shaped chain. */
        "fldcw %2\n\t"
        "fildll %3\n\t"
        "fildll %3\n\t"
        "fmull %4\n\t"
        ".byte 0xde,0xe9\n\t" /* source FSUBP ST(1),ST(0) */
        "fldcw %5\n\t"
        "fistpll %0\n\t"
        "fwait\n\t"
        "fnclex\n\t"
        "fldcw %2\n\t"
        "fnstcw %1\n\t"
        "fldcw %6\n\t"
        : "=m"(result), "=m"(restored)
        : "m"(control), "m"(raw), "m"(coefficient), "m"(truncation), "m"(saved)
        : "memory");
    *after=restored;
    return result;
}

int main(void) {
    unsigned i;
    for(i=0;i<CASE_COUNT;i++) {
        unsigned short after;
        uint64_t out=source_shape(CASES[i].raw,CASES[i].cw,&after);
        printf("%u %04x %08x%08x\n",i,(unsigned)after,(unsigned)(out>>32),(unsigned)out);
    }
    return 0;
}
