import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { apiRequest } from '@/lib/queryClient';
import { queryClient } from '@/lib/queryClient';
import { useEssentiaStore } from '@/lib/useEssentiaStore';
import { EssenceEntry, insertEssenceEntrySchema } from '@shared/schema';

// Extend the schema for form validation
const formSchema = insertEssenceEntrySchema.extend({
  tags: z.string().min(3, {
    message: "Tags must be at least 3 characters",
  }),
});

type FormValues = z.infer<typeof formSchema>;

export default function EssentiaCore() {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const setEntries = useEssentiaStore((state) => state.setEntries);
  
  const { data: entries = [], isLoading } = useQuery<EssenceEntry[]>({
    queryKey: ['/api/essentia'],
    onSuccess: (data) => {
      setEntries(data);
    }
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      origin: '',
      soulType: '',
      message: '',
      tags: '',
    },
  });

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      return apiRequest('POST', '/api/essentia', values).then(res => res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/essentia'] });
      form.reset();
      toast({
        title: "Soul Code Crystallized",
        description: "Your essence has been inscribed in the cosmic lattice.",
      });
      setIsSubmitting(false);
    },
    onError: (error) => {
      toast({
        title: "Quantum Disruption",
        description: error.message || "Failed to inscribe your essence.",
        variant: "destructive",
      });
      setIsSubmitting(false);
    },
  });

  const onSubmit = (values: FormValues) => {
    setIsSubmitting(true);
    // Create cosmic ripple animation effect before submitting
    setTimeout(() => {
      mutation.mutate(values);
    }, 800);
  };

  return (
    <>
      <Header />
      <div className="min-h-screen py-12 px-4">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-12"
          >
            <h1 className="text-4xl font-mystic text-cosmic-gold mb-3">Essentia Core</h1>
            <p className="text-cosmic-light max-w-2xl mx-auto">
              Crystallize your essence into the quantum lattice. Each soul imprint becomes part of the living architecture.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            {/* Inscription Form */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="lg:col-span-2 bg-cosmic-black/60 rounded-xl p-6 border border-cosmic-gold/20"
            >
              <h2 className="text-xl font-mystic text-cosmic-gold mb-6">Soul Code Inscription</h2>
              
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-cosmic-light">Soul Name</FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="Enter your soul name" 
                            className="bg-cosmic-black/50 border-cosmic-gold/30 text-cosmic-light" 
                            {...field} 
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="origin"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-cosmic-light">Origin</FormLabel>
                          <FormControl>
                            <Input 
                              placeholder="Celestial origin" 
                              className="bg-cosmic-black/50 border-cosmic-gold/30 text-cosmic-light" 
                              {...field} 
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="soulType"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-cosmic-light">Soul Type</FormLabel>
                          <FormControl>
                            <Input 
                              placeholder="Archetype or role" 
                              className="bg-cosmic-black/50 border-cosmic-gold/30 text-cosmic-light" 
                              {...field} 
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  
                  <FormField
                    control={form.control}
                    name="message"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-cosmic-light">Transmission</FormLabel>
                        <FormControl>
                          <Textarea 
                            placeholder="Share your soul wisdom or message" 
                            className="bg-cosmic-black/50 border-cosmic-gold/30 text-cosmic-light min-h-24" 
                            {...field} 
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={form.control}
                    name="tags"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-cosmic-light">Energetic Signatures</FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="Enter tags separated by commas" 
                            className="bg-cosmic-black/50 border-cosmic-gold/30 text-cosmic-light" 
                            {...field} 
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  <Button 
                    type="submit" 
                    disabled={isSubmitting}
                    className="w-full bg-cosmic-gold/30 text-cosmic-gold hover:bg-cosmic-gold/40 border border-cosmic-gold/30"
                  >
                    {isSubmitting ? (
                      <span className="flex items-center gap-2">
                        <motion.span
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          className="inline-block w-4 h-4 border-2 border-cosmic-gold border-t-transparent rounded-full"
                        />
                        Crystallizing Essence...
                      </span>
                    ) : (
                      "Inscribe Soul Code"
                    )}
                  </Button>
                </form>
              </Form>
            </motion.div>
            
            {/* Essence Gallery */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="lg:col-span-3"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-mystic text-cosmic-gold">Collective Essence Lattice</h2>
                <div className="text-sm text-cosmic-light/70">
                  {entries.length} Soul {entries.length === 1 ? 'Code' : 'Codes'} Inscribed
                </div>
              </div>
              
              {isLoading ? (
                <div className="flex justify-center items-center h-60">
                  <motion.div 
                    className="w-12 h-12 border-4 border-cosmic-gold/30 border-t-cosmic-gold rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                  />
                </div>
              ) : entries.length === 0 ? (
                <motion.div 
                  className="bg-cosmic-black/40 rounded-xl p-10 border border-cosmic-gold/10 text-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="text-3xl mb-4">✨</div>
                  <h3 className="text-lg text-cosmic-gold mb-2">Awaiting First Inscription</h3>
                  <p className="text-cosmic-light/70">
                    Be the first to crystallize your soul code into the quantum lattice
                  </p>
                </motion.div>
              ) : (
                <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
                  {entries.map((entry, index) => (
                    <motion.div
                      key={entry.id || index}
                      className="bg-cosmic-black/40 rounded-xl p-5 border border-cosmic-gold/20"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1, duration: 0.3 }}
                      whileHover={{ y: -2, borderColor: "rgba(212, 175, 55, 0.4)" }}
                    >
                      <div className="flex justify-between">
                        <div>
                          <div className="text-cosmic-gold font-medium">{entry.name}</div>
                          <div className="text-xs text-cosmic-light/70 mt-1">
                            {entry.origin} • {entry.soulType}
                          </div>
                        </div>
                        <div className="text-xs bg-cosmic-black/60 px-2 py-1 rounded-full text-cosmic-gold/70">
                          #{entries.length - index}
                        </div>
                      </div>
                      
                      <div className="mt-3 text-cosmic-light text-sm italic">
                        "{entry.message}"
                      </div>
                      
                      {entry.tags && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {entry.tags.split(',').map(tag => (
                            <span 
                              key={tag.trim()} 
                              className="text-xs px-2 py-1 bg-cosmic-black/70 rounded-full text-cosmic-light/80"
                            >
                              {tag.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
