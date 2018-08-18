class AbstractOptimiser:
   def process(self, graph):
        g = self.pre_process(graph)

        result = self.process_internal(g)

        return self.post_process(result)
   
   def pre_process(self, graph):
       return graph
   
   def process_internal(self, graph):
       return graph
   
   def post_process(self, result):
       return result


class DoubleNegativeOptimiser(AbstractOptimiser):
    # -(-a) -> a
    pass


class IntegerCostantsOptimiser(AbstractOptimiser):
    # a + 4*2 -> a + 8
    pass


class UnnecessaryOperationsOptimiser(AbstractOptimiser):
    # a * 0 -> 0
    # a + 0 -> 0
    # *   a or True -> True
    # *   a and False -> False
    pass

